<img width="1320" height="675" alt="스크린샷 2026-04-22 16 24 38" src="https://github.com/user-attachments/assets/85313df3-62eb-4ee4-b6e0-a37e0e223bcb" />

# DEMO
https://www.youtube.com/watch?v=RBNljPFehz4


**# English**

# Greenplum MCP-based Intelligent Operations Demo

This project demonstrates how to integrate data analytics and system operations in a Greenplum database environment using MCP (Model Context Protocol) and LLMs.

1. Using MCP, the LLM can analyze Greenplum schemas and data, generate SQL queries, and assist with data analysis.
   This enables the discovery of insights that may not be easily identified by human analysts.

2. MCP exposes Greenplum internal states (queries, segments, resources, etc.) in a format that LLMs can understand.
   Based on this, the system can automatically perform performance analysis, root cause inference, and generate operational insights.

## Key Features

* Sample data schema and data analysis
* Natural language to SQL generation and execution
* Report-style output based on query results
* Exposure of Greenplum system data via MCP APIs
* LLM-driven query and system analysis
* Segment status and resource usage monitoring
* Root cause analysis and operational guidance

## Architecture

OpenWebUI (chat/voice interface) → LLM → Greenplum Database → OpenWebUI (analysis results)

## Goals

1. Leverage AI to enhance the data analysis process and uncover hidden insights beyond traditional methods.
2. Move beyond simple monitoring and validate the feasibility of **autonomous database operations (AIOps)** using LLMs.


**#Korean**

<img width="949" height="475" alt="스크린샷 2026-04-22 16 18 57" src="https://github.com/user-attachments/assets/08c0e89c-f772-4182-8cfe-802d8d465d07" />

# DEMO
https://www.youtube.com/watch?v=RBNljPFehz4

# Greenplum MCP 기반 지능형 운영 데모

이 프로젝트는 Greenplum 데이터베이스 환경에서 MCP(Model Context Protocol)를 활용하여
데이터 분석과 시스템 상태와 쿼리 정보를 LLM과 직접 연동하는 데모입니다.

1. MCP를 통해 Greenplum의 스키마와 데이터를 분석하고 쿼리 작성 및 분석에 활용합니다.
   이를 기반으로 분석가가 확인하지 못한 데이터 인사이트를 발견합니다.
2. MCP를 통해 Greenplum의 내부 상태(쿼리, 세그먼트, 리소스 등)를 LLM이 이해할 수 있는 형태로 제공하고,
이를 기반으로 성능 분석, 장애 원인 추론, 운영 인사이트를 자동으로 도출합니다.

## 주요 기능
샘플 데이터 스키마 및 데이터 분석
자연어로 질의한 내용을 SQL로 작성하고 실행 결과 제공
출력 결과를 분석하여 리포트 형태로 출력
Greenplum 상태 정보를 MCP API로 제공
LLM 기반 쿼리 및 시스템 분석
세그먼트 상태 및 리소스 사용량 조회
장애 원인 추론 및 대응 가이드 생성

## 아키텍처

OpenWebUI(질의/chat,음성) → LLM -> Greenplum Database → OpenWebUI (분석 결과)

## 목적
1.데이터 분석 과정을 AI를 이용하여 미쳐 확인하지 못한 데이터 인사이트를 찾습니다.
2.단순 모니터링을 넘어,LLM을 활용한 자율형 데이터베이스 운영(AIOps) 가능성을 검증합니다.
