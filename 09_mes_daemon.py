import psycopg2
import time
import logging

# ---------------------------------------------------------
# 1. 환경 설정
# ---------------------------------------------------------
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'kbc',
    'user': 'gpadmin',
    'password': 'changeme'
}

BATCH_SIZE = 100            # 한 번의 사이클에 생성할 LOT 수
KEEP_LOTS = 50000           # 유지할 최대 LOT 개수 (이보다 오래된 lot_id는 삭제)
SLEEP_SECONDS = 60       # 사이클 대기 시간 (초)
VACUUM_CYCLE = 10            # 몇 사이클마다 VACUUM을 수행할지 결정

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def get_max_id(cursor, table_name, id_column):
    """테이블의 현재 MAX ID를 가져오는 헬퍼 함수"""
    cursor.execute(f"SELECT COALESCE(MAX({id_column}), 0) FROM {table_name}")
    return cursor.fetchone()[0]

def generate_mes_data(cursor):
    """DB 내장 함수를 활용한 병렬 더미 데이터 생성"""
    # 1. 현재 생성된 마지막 lot_id 확인
    start_lot_id = get_max_id(cursor, 'production_lot', 'lot_id') + 1
    end_lot_id = start_lot_id + BATCH_SIZE - 1

    logging.info(f"Generating LOT data: {start_lot_id} ~ {end_lot_id}...")

    # 2. production_lot 생성 (현재 날짜 기준)
    cursor.execute(f"""
        INSERT INTO production_lot
        SELECT
            gs AS lot_id,
            'LOT-' || to_char(gs, 'FM00000000') AS lot_number,
            (random()*9+1)::int AS product_id,
            (random()*4+1)::int AS equipment_id,
            CURRENT_DATE AS production_date,
            (random()*9000+1000)::int AS quantity,
            CASE WHEN random() < 0.92 THEN 'COMPLETED'
                 WHEN random() < 0.97 THEN 'IN_PROGRESS'
                 ELSE 'SCRAPPED' END AS status
        FROM generate_series({start_lot_id}, {end_lot_id}) gs;
    """)

    # 3. lot_material_usage 생성 (LOT당 3건)
    max_usage_id = get_max_id(cursor, 'lot_material_usage', 'id')
    cursor.execute(f"""
        INSERT INTO lot_material_usage
        SELECT
            {max_usage_id} + row_number() OVER() AS id,
            pl.lot_id,
            (random()*19+1)::int AS material_id,
            'MATLOT-' || to_char(pl.lot_id, 'FM000000') || '-' || gs,
            round((random()*500+50)::numeric, 2)
        FROM (SELECT lot_id FROM production_lot WHERE lot_id BETWEEN {start_lot_id} AND {end_lot_id}) pl,
             generate_series(1,3) gs;
    """)

    # 4. quality_inspection 생성 (LOT당 2건)
    max_insp_id = get_max_id(cursor, 'quality_inspection', 'inspection_id')
    cursor.execute(f"""
        INSERT INTO quality_inspection
        SELECT
            {max_insp_id} + row_number() OVER() AS inspection_id,
            pl.lot_id,
            CURRENT_TIMESTAMP + (random()*3 || ' hours')::interval,
            CASE WHEN random() < 0.7 THEN 'Voltage Test' ELSE 'Charge/Discharge Test' END,
            CASE WHEN random() < 0.95 THEN 'PASS' ELSE 'FAIL' END,
            round((random()*3)::numeric, 2)
        FROM (SELECT lot_id FROM production_lot WHERE lot_id BETWEEN {start_lot_id} AND {end_lot_id}) pl,
             generate_series(1,2);
    """)

    # 5. equipment_log 생성 (LOT당 10건)
    max_log_id = get_max_id(cursor, 'equipment_log', 'log_id')
    cursor.execute(f"""
        INSERT INTO equipment_log
        SELECT
            {max_log_id} + row_number() OVER() AS log_id,
            pl.lot_id,
            pl.equipment_id,
            CURRENT_TIMESTAMP + (gs || ' minutes')::interval,
            round((20 + random()*15)::numeric, 2),
            round((1 + random()*5)::numeric, 2),
            CASE WHEN random() < 0.98 THEN 'NORMAL' ELSE 'ALERT' END
        FROM (SELECT lot_id, equipment_id FROM production_lot WHERE lot_id BETWEEN {start_lot_id} AND {end_lot_id}) pl,
             generate_series(1,10) gs;
    """)

    # 6. shipments 생성 (70% 확률로 출하)
    max_ship_id = get_max_id(cursor, 'shipments', 'shipment_id')
    cursor.execute(f"""
        INSERT INTO shipments
        SELECT
            {max_ship_id} + row_number() OVER() AS shipment_id,
            pl.lot_id,
            (random()*9+1)::int,
            CURRENT_DATE + 2,
            (pl.quantity * 0.8)::int
        FROM (SELECT lot_id, quantity FROM production_lot WHERE lot_id BETWEEN {start_lot_id} AND {end_lot_id}) pl
        WHERE random() < 0.7;
    """)

    logging.info(f"[INSERT] Successfully generated data for {BATCH_SIZE} LOTs.")

def prune_old_data(cursor):
    """일정 용량(LOT 수) 유지를 위한 오래된 데이터 삭제"""
    max_lot_id = get_max_id(cursor, 'production_lot', 'lot_id')
    delete_threshold = max_lot_id - KEEP_LOTS

    if delete_threshold > 0:
        # 하위 테이블 먼저 삭제 (참조 무결성 로직 고려)
        tables = [
            'lot_material_usage',
            'quality_inspection',
            'equipment_log',
            'shipments',
            'production_lot'
        ]
        total_deleted = 0
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE lot_id <= {delete_threshold}")
            total_deleted += cursor.rowcount

        logging.info(f"[PRUNE] Deleted {total_deleted} old records (lot_id <= {delete_threshold}).")

def vacuum_tables(conn):
    """
    Greenplum의 AO 테이블은 DELETE 후 공간을 즉시 반환하지 않으므로 VACUUM 수행 필요.
    VACUUM은 트랜잭션 블록 외부에서 실행되어야 함 (autocommit 모드).
    """
    old_isolation = conn.isolation_level
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cursor:
            tables = ['production_lot', 'lot_material_usage', 'quality_inspection', 'equipment_log', 'shipments']
            for table in tables:
                logging.info(f"[VACUUM] Reclaiming storage for {table}...")
                cursor.execute(f"VACUUM {table};")
    finally:
        conn.set_isolation_level(old_isolation)

def run_daemon():
    logging.info("Starting MES Dummy Data Daemon...")
    cycle_count = 0

    while True:
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cursor:
                generate_mes_data(cursor)
                prune_old_data(cursor)

            # 트랜잭션 커밋
            conn.commit()
            cycle_count += 1

            # N주기마다 VACUUM 수행 (AO 테이블 용량 확보)
            if cycle_count % VACUUM_CYCLE == 0:
                vacuum_tables(conn)

        except Exception as e:
            logging.error(f"Error occurred: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    run_daemon()



  
#서비스 파일 생성
#sudo vi /etc/systemd/system/dummy-data-daemon.service
#[Unit]
#Description=Dummy Data Generator and Manager Daemon
#After=network.target mysql.service
#
#[Service]
#Type=simple
## 스크립트를 실행할 사용자
#User=ubuntu 
## Python 가상환경을 쓴다면 가상환경의 python 절대경로를 입력하세요.
#ExecStart=/usr/bin/python3 /path/to/your/daemon.py
#Restart=always
#RestartSec=10
#
#[Install]
#WantedBy=multi-user.target

  
#데몬 실행 및 자동 시작 등록
#sudo systemctl daemon-reload
#sudo systemctl enable dummy-data-daemon
#sudo systemctl start dummy-data-daemon
