# MCP Mock Server - Technical Specification

## 📋 Executive Summary

MCP Mock Server는 **FastMCP**와 **FastAgent** 프레임워크를 기반으로 구축된 모듈형 도구 서버입니다.
외부 API(검색, 날씨 등)와 데이터베이스(Oracle, Milvus)를 통합하여
AI 에이전트가 활용할 수 있는 MCP(Model Context Protocol) 표준 인터페이스를 제공합니다.

### Key Features

-   **MCP 표준 준수**: Model Context Protocol을 통한 표준화된 도구 제공
-   **멀티 서버 아키텍처**: MCP Server와 Agent Server의 분리된 구조
-   **확장 가능한 도구 시스템**: 플러그인 방식의 도구 등록 및 관리
-   **벡터 DB 통합**: Milvus를 활용한 임베딩 검색 지원
-   **관계형 DB 연동**: Oracle DB 쿼리 도구 제공

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│                  (AI Applications, APIs)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Request
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAgent Server                          │
│                    (Port: 9090)                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Agent: Agent_Search                                 │   │
│  │  - Model: Google Gemini 2.5 Flash                   │   │
│  │  - MCP Clients: mcp-mock-server, duckduckgo, etc.  │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol (HTTP)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastMCP Server                            │
│                    (Port: 9092)                              │
│  ┌────────────┬────────────┬────────────┬──────────────┐    │
│  │  Google    │  Weather   │  Milvus    │  Oracle      │    │
│  │  Search    │  API       │  Search    │  Query       │    │
│  └────────────┴────────────┴────────────┴──────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────────┐
         ▼               ▼                   ▼
┌─────────────┐  ┌─────────────┐   ┌──────────────────┐
│  External   │  │  Milvus     │   │  Oracle DB       │
│  APIs       │  │  Vector DB  │   │  (Port: 1521)    │
│             │  │  (Port:     │   │                  │
│             │  │   19530)    │   │                  │
└─────────────┘  └─────────────┘   └──────────────────┘
```

### Component Breakdown

#### 1. FastAgent Server (`agents/agent_server.py`)

-   **역할**: AI 에이전트 오케스트레이션 레이어
-   **포트**: 9090
-   **주요 기능**:
    -   LLM 모델과의 인터페이스 제공
    -   여러 MCP 서버를 클라이언트로 연결
    -   도구 선택 및 실행 로직 관리
    -   스트리밍 응답 지원

#### 2. FastMCP Server (`/mcp_server.py`)

-   **역할**: 도구 제공자 (Tool Provider)
-   **포트**: 9092
-   **주요 기능**:
    -   MCP 프로토콜 엔드포인트 제공 (`/mcp`)
    -   도구 등록 및 메타데이터 관리
    -   리소스 등록 (시스템 상태 등)
    -   CORS 설정 및 HTTP 미들웨어

---

## 🧩 MCP, FastMCP, FastAgent 이해하기

### MCP (Model Context Protocol)란?

**MCP**는 Anthropic이 제안한 **AI 모델과 외부 도구 간의 표준 통신 프로토콜**입니다.

#### 핵심 개념:

1. **표준화된 인터페이스**: LLM이 다양한 도구(API, DB, 파일 시스템 등)를 일관된 방식으로 사용
2. **도구 제공자와 소비자 분리**:
   - **Server**: 도구를 제공하는 측 (Tool Provider)
   - **Client**: 도구를 사용하는 측 (LLM Agent)
3. **프로토콜 계층**:
   ```
   LLM Application (Claude, GPT, etc.)
        ↓
   MCP Client (도구 요청)
        ↓ MCP Protocol (JSON-RPC)
   MCP Server (도구 제공)
        ↓
   External Resources (API, DB, etc.)
   ```

#### MCP가 해결하는 문제:

- ❌ **이전**: 각 도구마다 다른 API 형식, 인증 방식, 에러 처리
- ✅ **MCP**: 모든 도구가 동일한 스키마와 호출 규약 사용

### FastMCP: MCP Server 구현 프레임워크

**FastMCP**는 MCP 서버를 쉽게 구축하기 위한 Python 프레임워크입니다.

#### 왜 FastMCP를 선택했는가?

1. **간편한 도구 등록**: 데코레이터 기반으로 함수를 도구로 변환
2. **자동 스키마 생성**: Python 타입 힌트 → MCP 스키마 자동 변환
3. **HTTP/SSE 지원**: 다양한 전송 프로토콜 지원
4. **FastAPI 통합**: 기존 FastAPI 애플리케이션에 쉽게 통합

#### FastMCP 동작 원리:

```python
# mcp_server.py
from fastmcp import FastMCP

mcp = FastMCP("mcp-mock-server")

@mcp.tool()
def google_search(query: str, maxResults: int = 1) -> dict:
    """구글 검색을 수행합니다."""
    # 실제 구현...
    return {"title": "...", "link": "...", "snippet": "..."}
```

**FastMCP가 자동으로 처리하는 것:**

1. **Input Schema 생성**:
   ```json
   {
     "name": "google_search",
     "description": "구글 검색을 수행합니다.",
     "inputSchema": {
       "type": "object",
       "properties": {
         "query": {"type": "string"},
         "maxResults": {"type": "integer", "default": 1}
       },
       "required": ["query"]
     }
   }
   ```

2. **Output Schema 생성**:
   ```json
   {
     "content": [
       {
         "type": "text",
         "text": "{\"title\": \"...\", \"link\": \"...\", \"snippet\": \"...\"}"
       }
     ]
   }
   ```

3. **MCP 엔드포인트 노출**:
   - `/mcp` - MCP 프로토콜 엔드포인트
   - Tool 목록 조회, 실행, 결과 반환 자동 처리

### FastAgent: MCP Client 구현 프레임워크

**FastAgent**는 여러 MCP 서버를 통합하여 LLM 기반 에이전트를 구축하는 프레임워크입니다.

#### 왜 FastAgent를 선택했는가?

1. **멀티 MCP 서버 연결**: 여러 MCP 서버의 도구를 하나의 에이전트에서 사용
2. **LLM 통합**: Google Gemini, OpenAI 등 다양한 LLM 모델 지원
3. **도구 오케스트레이션**: LLM이 자동으로 적절한 도구 선택 및 실행
4. **스트리밍 지원**: 실시간 응답 스트리밍 (Markdown, JSON 등)

#### FastAgent 동작 원리:

```yaml
# agents/fastagent.config.yaml
default_model: google.gemini-2.5-flash

mcp:
  servers:
    mcp-mock-server:
      transport: http
      url: http://127.0.0.1:9092/mcp
    duckduckgo:
      command: "uvx"
      args: ["ddg-mcp-server"]
```

**FastAgent가 자동으로 처리하는 것:**

1. **MCP 서버 연결**:
   - HTTP 기반 MCP 서버 연결 (`mcp-mock-server`)
   - 로컬 프로세스 기반 MCP 서버 실행 (`duckduckgo`)

2. **도구 목록 통합**:
   ```
   Available Tools:
   - google_search (from mcp-mock-server)
   - oracle_query (from mcp-mock-server)
   - milvus_search (from mcp-mock-server)
   - duckduckgo_search (from duckduckgo)
   ```

3. **LLM과 도구 연결**:
   - 사용자 질문을 LLM에게 전달
   - LLM이 필요한 도구를 선택하고 파라미터 생성
   - MCP 프로토콜로 도구 실행
   - 결과를 LLM에게 다시 전달
   - 최종 답변 생성

### 본 프로젝트의 아키텍처 흐름

#### 1. 사용자 요청 처리

```
사용자: "Alice의 잔액을 조회해줘"
   ↓
FastAgent (Port 9090)
   ↓ [LLM이 도구 선택]
   ↓ "milvus_search 도구 사용 결정"
   ↓
MCP Protocol 호출
```

#### 2. MCP Protocol 통신

**Request** (Agent → MCP Server):
```json
POST http://localhost:9092/mcp/tools/milvus_search
Content-Type: application/json

{
  "method": "tools/call",
  "params": {
    "name": "milvus_search",
    "arguments": {
      "intent": "잔액 조회",
      "top_k": 1
    }
  }
}
```

**Response** (MCP Server → Agent):
```json
{
  "content": [
    {
      "type": "text",
      "text": "SELECT balance FROM deposit WHERE account_holder = '{name}'"
    }
  ],
  "isError": false
}
```

#### 3. Input/Output Schema 맞추기

##### 예제 1: Milvus Search 도구

**도구 정의** (`mcp_servers/tools/query/milvus_search.py`):
```python
def milvus_search(intent: str, top_k: int = 1) -> ToolResult:
    # ... 구현 ...
    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=sql_template  # str
            )
        ],
        structured_content={
            "intent_description": intent_description,
            "sql_template": sql_template,
            "similarity_score": score
        }
    )
```

**FastMCP 자동 생성 스키마**:
```json
{
  "name": "milvus_search",
  "description": "Milvus에서 쿼리와 유사한 SQL 템플릿을 검색합니다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "intent": {
        "type": "string",
        "description": "검색할 쿼리 문자열"
      },
      "top_k": {
        "type": "integer",
        "default": 1,
        "description": "검색할 상위 K개 결과 수"
      }
    },
    "required": ["intent"]
  }
}
```

**Output Format**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "SELECT balance FROM deposit WHERE account_holder = '{name}'"
    }
  ],
  "structured_content": {
    "intent_description": "계좌 잔액 조회",
    "sql_template": "SELECT balance FROM deposit WHERE account_holder = '{name}'",
    "similarity_score": 0.95
  }
}
```

##### 예제 2: Oracle Query 도구

**도구 정의** (`mcp_servers/tools/query/oracle_query.py`):
```python
def oracle_query(query: str) -> ToolResult:
    # ... 구현 ...
    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False)
            )
        ],
        structured_content=result
    )
```

**Input Schema**:
```json
{
  "name": "oracle_query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "실행할 SQL 쿼리"
      }
    },
    "required": ["query"]
  }
}
```

**Output Format**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"rows\": [{\"balance\": 1000}], \"rowCount\": 1}"
    }
  ],
  "structured_content": {
    "rows": [{"balance": 1000}],
    "rowCount": 1
  }
}
```

### Schema 일관성 유지 전략

#### 1. ToolResult 표준 사용

모든 도구는 `ToolResult` 객체를 반환:
```python
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

ToolResult(
    content=[TextContent(type="text", text="...")],  # 필수: 텍스트 응답
    structured_content={...}  # 선택: 구조화된 데이터
)
```

#### 2. 타입 힌트 활용

Python 타입 힌트를 사용하여 자동 스키마 생성:
```python
def tool_name(
    param1: str,           # required string
    param2: int = 10,      # optional integer with default
    param3: list[str] = [] # optional list
) -> ToolResult:
    pass
```

#### 3. 공통 타입 정의

`mcp_servers/types.py`에서 공통 타입 정의:
```python
from typing import TypedDict

class QueryResult(TypedDict):
    rows: list[dict]
    rowCount: int
```

### FastMCP vs FastAgent 비교

| 구분 | FastMCP | FastAgent |
|------|---------|-----------|
| **역할** | MCP Server (도구 제공자) | MCP Client (도구 소비자) |
| **포트** | 9092 | 9090 |
| **주요 기능** | 도구 등록, 실행, 결과 반환 | LLM 통합, 도구 선택, 오케스트레이션 |
| **입력** | MCP Protocol 요청 | 사용자 자연어 질문 |
| **출력** | MCP Protocol 응답 | 자연어 답변 (스트리밍) |
| **연결 대상** | 외부 API, DB | 여러 MCP 서버 |
| **설정 파일** | `mcp_server.py` | `fastagent.config.yaml` |

### 실제 요청/응답 흐름 예시

#### 전체 흐름:

```
[사용자] "Alice의 잔액 조회"
   ↓
[FastAgent] POST /chat
   ↓ LLM 분석
   ↓ 도구: milvus_search 선택
   ↓ MCP 요청 생성
   ↓
[FastMCP] POST /mcp/tools/milvus_search
   ↓ 도구 실행
   ↓ Milvus 검색
   ↓ SQL 템플릿 반환
   ↓
[FastAgent] MCP 응답 수신
   ↓ LLM에게 전달
   ↓ LLM이 파라미터 바인딩
   ↓ 도구: oracle_query 선택
   ↓
[FastMCP] POST /mcp/tools/oracle_query
   ↓ 도구 실행
   ↓ Oracle DB 쿼리
   ↓ 결과 반환
   ↓
[FastAgent] MCP 응답 수신
   ↓ LLM에게 전달
   ↓ 자연어 답변 생성
   ↓
[사용자] "Alice님의 잔액은 1,000원입니다."
```

#### 실제 HTTP 요청 예시:

**Step 1: 사용자 → FastAgent**
```http
POST http://localhost:9090/chat
Content-Type: application/json

{
  "message": "Alice의 잔액을 조회해줘"
}
```

**Step 2: FastAgent → FastMCP (Milvus)**
```http
POST http://localhost:9092/mcp/tools/milvus_search
Content-Type: application/json

{
  "method": "tools/call",
  "params": {
    "name": "milvus_search",
    "arguments": {
      "intent": "잔액 조회",
      "top_k": 1
    }
  }
}
```

**Step 3: FastMCP → FastAgent (Milvus 결과)**
```json
{
  "content": [{
    "type": "text",
    "text": "SELECT balance FROM deposit WHERE account_holder = '{name}'"
  }],
  "structured_content": {
    "intent_description": "계좌 잔액 조회",
    "sql_template": "SELECT balance FROM deposit WHERE account_holder = '{name}'",
    "similarity_score": 0.95
  }
}
```

**Step 4: FastAgent → FastMCP (Oracle)**
```http
POST http://localhost:9092/mcp/tools/oracle_query
Content-Type: application/json

{
  "method": "tools/call",
  "params": {
    "name": "oracle_query",
    "arguments": {
      "query": "SELECT balance FROM deposit WHERE account_holder = 'Alice'"
    }
  }
}
```

**Step 5: FastMCP → FastAgent (Oracle 결과)**
```json
{
  "content": [{
    "type": "text",
    "text": "{\"rows\": [{\"balance\": 1000}], \"rowCount\": 1}"
  }],
  "structured_content": {
    "rows": [{"balance": 1000}],
    "rowCount": 1
  }
}
```

**Step 6: FastAgent → 사용자 (최종 답변)**
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

data: {"type": "message", "content": "Alice님의 잔액은 1,000원입니다."}
```

### 핵심 장점

1. **확장성**: 새로운 도구를 `@mcp.tool()` 데코레이터만 추가하면 즉시 사용 가능
2. **표준화**: 모든 도구가 동일한 MCP 프로토콜 사용
3. **분리**: MCP Server와 Agent Server가 독립적으로 배포 가능
4. **재사용성**: 다른 MCP Client에서도 동일한 도구 사용 가능
5. **타입 안전성**: Python 타입 힌트 → 자동 검증

---

## 🔧 Technical Stack

### Core Dependencies

| Package            | Version  | Purpose                   |
| ------------------ | -------- | ------------------------- |
| **Python**         | 3.13+    | Runtime Environment       |
| **fastmcp**        | 2.13.1+  | MCP Server Framework      |
| **fast-agent-mcp** | 0.2.25+  | Agent Orchestration       |
| **fastapi**        | 0.123.0+ | HTTP Server Framework     |
| **google-genai**   | 1.52.0+  | LLM Model Integration     |
| **pymilvus**       | 2.6.4+   | Vector Database Client    |
| **oracledb**       | 3.4.1+   | Oracle Database Driver    |
| **python-dotenv**  | 1.2.1+   | Environment Configuration |

### Infrastructure (Docker Compose)

| Service       | Image                       | Ports       | Purpose               |
| ------------- | --------------------------- | ----------- | --------------------- |
| **Milvus**    | milvusdb/milvus:v2.6.6      | 19530, 9091 | Vector Database       |
| **etcd**      | quay.io/coreos/etcd:v3.5.18 | 2379        | Milvus Metadata Store |
| **MinIO**     | minio/minio:latest          | 9000, 9001  | Milvus Object Storage |
| **Attu**      | zilliz/attu:latest          | 8000        | Milvus Web UI         |
| **Oracle DB** | oracle/database:19.3.0-ee   | 1521        | Relational Database   |

---

## 🛠️ Tool Registry

### Implemented Tools

#### 1. Google Search (`google_search`)

**File**: `mcp_servers/tools/search/google_search.py`

```python
async def google_search(inputs: dict) -> ToolResult
```

**Parameters**:

-   `query` (str): 검색 쿼리
-   `maxResults` (int, optional): 최대 결과 수 (기본값: 1)

**Returns**:

-   `title`: 검색 결과 제목
-   `link`: 검색 결과 URL
-   `snippet`: 검색 결과 요약

**External API**: Google Custom Search API

-   Endpoint: `https://www.googleapis.com/customsearch/v1`
-   API Key: `GOOGLE_WEB_SEARCH_API_KEY`

---

#### 2. Open Weather Map (`open_weather_map`)

**File**: `mcp_servers/tools/weather/open_weather_map.py`

**External API**: OpenWeatherMap API

-   Endpoint: `http://api.openweathermap.org/data/2.5/weather`
-   API Key: `OPEN_WEATHER_MAP_API_KEY`

---

#### 3. Web Content Fetcher (`fetch_and_parse`)

**File**: `mcp_servers/tools/search/web_content_fetch.py`

**Status**: 미등록, 구현 미완료

**Purpose**: URL의 웹 페이지 콘텐츠를 가져와서 파싱

---

#### 4. DuckDuckGo Search (`duckduckgo_search`)

**File**: `mcp_servers/tools/search/duckduckgo_search.py`

**Status**: 미등록, 구현 미완료

**Note**: FastAgent에서 직접 `ddg-mcp-server` 사용 중

---

#### 5. Oracle Query (`oracle_query`)

**File**: `mcp_servers/tools/query/oracle_query.py`

**Status**: 🚧 등록됨, 구현 완료

**Purpose**: Oracle DB에 대한 SQL 쿼리 실행

**Database Connection**:

-   Connection Pool: `oracledb.create_pool()`
-   Pool Size: min=2, max=4, increment=1
-   Connection String: `ORACLE_DSN`

---

#### 6. Milvus Search (`milvus_search`)

**File**: `mcp_servers/tools/query/milvus_search.py`

**Status**: 🚧 등록됨, 구현 완료

**Purpose**: Milvus 벡터 DB에서 자연어 의도와 유사한 SQL 템플릿을 검색

```python
def milvus_search(intent: str, top_k: int = 1) -> ToolResult
```

**Parameters**:

-   `intent` (str): 검색할 자연어 쿼리 (예: "잔액 조회")
-   `top_k` (int, optional): 반환할 상위 결과 개수 (기본값: 1)

**Returns**:

-   `intent_description`: 검색된 의도 설명
-   `sql_template`: 해당 SQL 템플릿
-   `similarity_score`: 코사인 유사도 점수

**Database Connection**:

-   Client: `MilvusClient(uri="http://localhost:19530")`
-   Collection: `my_collection`
-   Embedding Model: `sentence-transformers/all-MiniLM-L6-v2`
-   Metric Type: COSINE

**특징**:

-   자연어 의도를 벡터로 임베딩하여 유사한 SQL 템플릿 검색
-   벡터 검색을 통해 의미적으로 유사한 쿼리 매칭
-   Oracle Query와 함께 사용하여 자연어 → SQL 변환 가능

---

## 🔐 Configuration Management

### Environment Variables (`.env.local`)

```bash
# Google Search API
GOOGLE_WEB_SEARCH_URL=https://www.googleapis.com/customsearch/v1
GOOGLE_WEB_SEARCH_API_KEY=<your-api-key>

# OpenWeatherMap API
OPEN_WEATHER_MAP_API_KEY=<your-api-key>

# DuckDuckGo (if needed)
DUCKDUCKGO_BASE_URL=https://html.duckduckgo.com/html

# Oracle Database
ORACLE_USER=<username>
ORACLE_PASSWORD=<password>
ORACLE_DSN=localhost:1521/ORCL

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### FastAgent Configuration (`agents/fastagent.config.yaml`)

**Key Configurations**:

1. **Default Model**:

    ```yaml
    default_model: google.gemini-2.5-flash
    ```

2. **MCP Server Connections**:

    ```yaml
    mcp:
        servers:
            mcp-mock-server:
                transport: http
                url: http://127.0.0.1:9091/mcp
            duckduckgo:
                command: "uvx"
                args: ["ddg-mcp-server"]
    ```

    MCP 서버 연결 방법

    1. 커맨드 실행 방식 (command + args)

    - 로컬에서 실행 가능한 프로그램(명령어)을 호출해서 mcp 서버 프로세스를 직접 기동

    2. URL 기반 연결

    - Agent가 해당 `url`로 HTTP 요청 등(구현에 따라 다름)을 통해 통신

3. **Logger Settings**:
    ```yaml
    logger:
        progress_display: true
        show_chat: true
        show_tools: true
        streaming: markdown
    ```

### FastAgent Secrets (`agents/fastagent.secrets.yaml`)

```yaml
# Google Gemini
google:
    api_key: "<your-gemini-api-key>"
# OpenAI (optional)
# openai:
#   api_key: "<your-openai-api-key>"
```

---

## 🚀 Deployment Guide

### Local Development

#### 1. Prerequisites

```bash
# Python 3.13+ 설치 확인
python --version

# UV 패키지 매니저 설치 (권장)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. Environment Setup

```bash
# 가상 환경 생성 및 활성화
uv venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env.local
# .env.local 파일 작성

# FastAgent Secrets 설정
# agents/fastagent.secrets.yaml 파일 생성 및 API 키 입력
```

#### 3. Start Infrastructure

```bash
# Docker Compose로 인프라 서비스 실행
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

#### 4. Start Servers

**Terminal 1 - MCP Server**:

```bash
fastmcp run mcp_server.py:mcp --transport http --port 9092
```

**Terminal 2 - Agent Server**:

```bash
cd agents
uv run agent_server.py --transport http --port 9090
```

**Terminal 3 - DB Init**:

Milvus, Oracle DB에 초기 데이터를 설정합니다.

```bash
uvicorn db.db_server:app --host 0.0.0.0 --port 9093
```

### Production Deployment Considerations

1. **환경 분리**: `.env.local` → `.env.production`
2. **보안**:
    - API 키를 환경 변수로 관리 (Secrets Manager 사용 권장)
    - CORS 설정 강화 (`CORS_ORIGINS`)
    - Rate Limiting 적용 (`utils/rate_limiter.py`)
3. **스케일링**:
    - Uvicorn workers 증가
    - Oracle Connection Pool 크기 조정
    - Milvus 클러스터 모드 고려
4. **모니터링**:
    - FastAgent logger를 파일/HTTP로 전환
    - Docker 컨테이너 헬스체크 활성화

---

## 📊 Data Flow

### Example 1: Google Search Request

```
1. Client → Agent Server
   POST http://localhost:9090/chat
   Body: {"message": "파이썬이란?"}

2. Agent Server → LLM (Gemini 2.5 Flash)
   - 사용자 질문 분석
   - 필요한 도구 선택: "google_search"

3. Agent Server → MCP Server
   POST http://localhost:9092/mcp/tools/google_search
   Body: {"query": "파이썬이란", "maxResults": 1}

4. MCP Server → Google API
   GET https://www.googleapis.com/customsearch/v1
   Params: {key: <api-key>, cx: <search-id>, q: "파이썬이란"}

5. Google API → MCP Server
   Response: {items: [{title, link, snippet}]}

6. MCP Server → Agent Server
   Response: {title, link, snippet}

7. Agent Server → LLM
   - 검색 결과를 컨텍스트로 제공
   - 최종 답변 생성

8. Agent Server → Client
   Response: "파이썬은 ... [검색 결과 기반 답변]"
```

### Example 2: Natural Language to SQL Query (Milvus + Oracle)

```
1. Client → Agent Server
   POST http://localhost:9090/chat
   Body: {"message": "Alice의 잔액을 조회해줘"}

2. Agent Server → LLM (Gemini 2.5 Flash)
   - 사용자 질문 분석
   - 필요한 도구 선택: "milvus_search" (자연어 → SQL 변환)

3. Agent Server → MCP Server (Milvus Search)
   POST http://localhost:9092/mcp/tools/milvus_search
   Body: {"intent": "잔액 조회", "top_k": 1}

4. MCP Server → Milvus Vector DB
   - "잔액 조회" 텍스트를 임베딩 벡터로 변환
   - 코사인 유사도 검색 수행
   Collection: my_collection
   Search Vector: [0.123, -0.456, ...] (384차원)

5. Milvus → MCP Server
   Response: {
     "intent_description": "계좌 잔액 조회",
     "sql_template": "SELECT balance FROM deposit WHERE account_holder = '{name}'",
     "similarity_score": 0.95
   }

6. MCP Server → Agent Server
   Response: SQL 템플릿 반환

7. Agent Server → LLM
   - SQL 템플릿에 파라미터 바인딩
   - 필요한 도구 선택: "oracle_query"

8. Agent Server → MCP Server (Oracle Query)
   POST http://localhost:9092/mcp/tools/oracle_query
   Body: {"query": "SELECT balance FROM deposit WHERE account_holder = 'Alice'"}

9. MCP Server → Oracle DB
   - Connection Pool에서 연결 가져오기
   - SQL 쿼리 실행
   DSN: localhost:1521/ORCL

10. Oracle DB → MCP Server
    Response: {rows: [{balance: 1000}]}

11. MCP Server → Agent Server
    Response: {balance: 1000}

12. Agent Server → LLM
    - 쿼리 결과를 자연어로 변환

13. Agent Server → Client
    Response: "Alice님의 잔액은 1,000원입니다."
```

---

## 🗄️ Database Schema

### Milvus (Vector Database)

**Purpose**: 임베딩 벡터 저장 및 유사도 검색

**초기화 스크립트**: `db/db_server.py`

**Milvus 초기화**: `db/milvus_init.py`

**Connection**:

```python
from pymilvus import MilvusClient
client = MilvusClient(uri="http://localhost:19530")
```

**Collection**: `my_collection`

**Schema**:

-   `id`: Primary Key
-   `vector`: 임베딩 벡터 (384 차원)
-   `intent_description`: 의도 설명 (VARCHAR)
-   `sql_template`: SQL 템플릿 (TEXT)

---

### Oracle Database

**Purpose**: 관계형 데이터 저장 및 SQL 쿼리

**초기화 서버**: `db/db_server.py`

**Oracle 초기화**: `db/oracle_init.py`

**Connection Pool**: `mcp_servers/db/oracle.py`

```python
db_pool = oracledb.create_pool(
    user=ORACLE_USER,
    password=ORACLE_PASSWORD,
    dsn=ORACLE_DSN,
    min=2, max=4, increment=1
)
```

**Schema**: `db/oracle_schema.py`

**테이블**:

-   `deposit`: 예금 계좌 정보
    -   `account_holder`: 계좌 소유자 (VARCHAR2)
    -   `balance`: 잔액 (NUMBER)

---

## 🧪 Testing Strategy

### Unit Testing

-   **대상**: 각 도구 함수 (`google_search`, `open_weather_map`, etc.)
-   **프레임워크**: pytest (권장)
-   **Mock**: External API 호출은 Mock 처리

### Integration Testing

-   **대상**: MCP Server ↔ Agent Server 통신
-   **시나리오**:
    1. 도구 목록 조회
    2. 도구 실행 및 응답 검증
    3. 에러 핸들링

### End-to-End Testing

-   **시나리오**: 사용자 질문 → 검색 → 응답 생성
-   **검증 항목**:
    -   응답 시간 (< 5초)
    -   응답 정확도
    -   에러 복구

---

## 🔍 Monitoring & Observability

### Logging

**FastAgent Logger**:

-   **위치**: `agents/fastagent.config.yaml`
-   **현재 설정**: Console + Markdown Streaming
-   **권장 개선**:
    ```yaml
    logger:
        type: "file"
        path: "/var/log/fastagent/agent.jsonl"
    ```

**FastMCP Logger**:

-   **현재 설정**: `log_level='DEBUG'` (server.py:41)
-   **권장**: Production에서는 `INFO` 레벨 사용

### Health Checks

**MCP Server**:

```bash
curl http://localhost:9092/health
```

**Agent Server**:

```bash
curl http://localhost:9090/health
```

**Database Services**:

-   Milvus: `curl http://localhost:9091/healthz`
-   MinIO: `curl http://localhost:9000/minio/health/live`
-   Oracle: Connection pool status check

### Milvus 관리 페이지 접속

**Milvus Attu:**

`http://localhost:8000/` 접속

`milvus address`에 `http://mivlus-standalone:19530`을 입력한 후, connect를 클릭합니다.

**Milvus Webui:**

`http://localhost:9091/webui/` 접속

## 🚧 Known Issues & Limitations

### Current Status

| 항목                | 상태           | 비고                  |
| ------------------- | -------------- | --------------------- |
| Google Search       | ✅ 구현 완료   | API 키 필수           |
| OpenWeatherMap      | ✅ 구현 완료   | API 키 필수           |
| Web Content Fetcher | 미등록, 미구현 | BeautifulSoup 등 필요 |
| DuckDuckGo Search   | 미등록, 미구현 | Agent에서 직접 연결   |
| Oracle Query        | ✅ 구현 완료   | SQL 실행 로직 필요    |
| Milvus Search       | ✅ 구현 완료   | ReRank 필요           |

### Technical Debt

1. **에러 핸들링**: 일부 도구에서 예외 처리 미흡
2. **테스트 코드**: 단위 테스트 부재
3. **API Rate Limiting**: `rate_limiter.py` 존재하나 미적용
4. **보안**: API 키가 코드에 하드코딩된 부분 존재 (google_search.py:39)
5. **문서화**: API 문서 자동 생성 미설정 (FastAPI /docs 활성화 권장)

---

## 🛣️ Roadmap

### Phase 1: Core Stability (Current)

-   [x] MCP Server 기본 구조 구축
-   [x] Google Search 도구 구현
-   [x] Weather API 도구 구현
-   [ ] 에러 핸들링 강화
-   [ ] 단위 테스트 작성

### Phase 2: Feature Completion

-   [ ] Web Content Fetcher 구현
-   [ ] Oracle Query 도구 완성
-   [ ] Milvus 임베딩 검색 도구 구현
-   [ ] System Status Resource 구현
-   [ ] Rate Limiting 적용

### Phase 3: Production Ready

-   [ ] API 문서 자동화 (FastAPI /docs)
-   [ ] 통합 테스트 작성
-   [ ] 로깅 시스템 강화
-   [ ] Docker 이미지 최적화
-   [ ] CI/CD 파이프라인 구축

### Phase 4: Advanced Features

-   [ ] 도구 캐싱 레이어
-   [ ] 멀티모달 도구 지원 (이미지 검색 등)
-   [ ] 커스텀 프롬프트 템플릿 시스템
-   [ ] 웹 UI 대시보드

---

## 📚 References

### Official Documentation

-   [FastMCP Documentation](https://github.com/jlowin/fastmcp)
-   [FastAgent Documentation](https://github.com/anthropics/fast-agent-mcp)
-   [Model Context Protocol Spec](https://modelcontextprotocol.io/)
-   [Milvus Documentation](https://milvus.io/docs/)

### API Documentation

-   [Google Custom Search API](https://developers.google.com/custom-search/v1/overview)
-   [OpenWeatherMap API](https://openweathermap.org/api)
-   [Oracle Python Driver](https://python-oracledb.readthedocs.io/)

---

## 👥 Development Team Contacts

### Project Maintainer

-   **Name**: [Your Name]
-   **Email**: [Your Email]
-   **Role**: Lead Developer

### Contributors

-   [List team members and their roles]

---

## 📝 License

[Specify License - e.g., MIT, Apache 2.0]

---

**Last Updated**: 2025-12-09
**Document Version**: 1.0.0

sh-4.4$ sqlplus SYSTEM/oracleadmin@ORCLPDB1

SQL\*Plus: Release 19.0.0.0.0 - Production on Wed Dec 24 08:34:10 2025
Version 19.19.0.0.0

Copyright (c) 1982, 2023, Oracle. All rights reserved.

Last Successful login time: Wed Dec 24 2025 08:33:01 +00:00

Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.19.0.0.0

SQL> SELECT balance FROM deposit WHERE account_holder = 'Alice';

## BALANCE

      1000

## TODO

추천 방식: 이전에 말씀드린 cryptography 라이브러리를 써서,
.env 파일에 암호화된 값을 넣고 코드 시작 시점에만 복호화해서 사용하는 것이
현재 mcp-mock-server 환경에서 가장 현실적인 보안 적용법입니다.
