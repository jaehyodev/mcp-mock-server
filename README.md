# MCP Mock Server

이 프로젝트는 `FastMCP, FastAgent` 프레임워크를 사용하여 구축된 Mock 서버입니다. 다양한 외부 도구(검색, 날씨 등)를 통합하여 API 형태로 제공합니다.

## 🤖 프로젝트 정보

-   **프로젝트 이름**: mcp-mock-server
-   **Python 버전**: 3.13+
-   **주요 프레임워크**: FastAPI, FastMCP, FastAgent

## 📂 프로젝트 구조

```
/
├── .env.example              # 환경 변수 예제 파일
├── .gitignore                # Git 제외 파일 목록
├── docker-compose.yml        # Docker Compose 설정 파일
├── pyproject.toml            # 프로젝트 의존성 및 설정 파일
├── README.md                 # 프로젝트 설명 파일
├── SPEC.md                   # 프로젝트 기술 명세서
├── mcp_server.py             # FastMCP 서버 실행 파일
├── agents/                   # FastAgent 관련 파일
│   ├── agent_server.py       # FastAgent 서버 실행 파일
│   ├── fastagent.config.yaml # FastAgent 설정 파일
│   └── fastagent.secrets.yaml # FastAgent API 키 설정 파일
├── db/                       # 데이터베이스 초기화 관련 파일
│   ├── config/               # DB 설정 파일
│   │   └── settings.py       # 환경 변수 로딩
│   ├── db_server.py          # DB 초기화 서버 (FastAPI)
│   ├── milvus_init.py        # Milvus 초기화 스크립트
│   ├── oracle_init.py        # Oracle 초기화 스크립트
│   └── oracle_schema.py      # Oracle 스키마 정의
├── mcp_servers/              # FastMCP 서버 관련 파일
│   ├── config/               # MCP 서버 설정 관련 파일
│   │   └── settings.py       # 환경 변수 로딩
│   ├── db/                   # 데이터베이스 연결 파일
│   │   └── oracle.py         # Oracle 연결 풀 관리
│   ├── types.py              # 공통 타입 정의
│   └── tools/                # FastMCP에 등록될 도구들
│       ├── query/            # 데이터베이스 쿼리 관련 도구
│       │   ├── milvus_search.py  # Milvus 벡터 검색 도구
│       │   └── oracle_query.py   # Oracle SQL 쿼리 도구
│       ├── search/           # 검색 관련 도구
│       │   ├── duckduckgo_search.py
│       │   ├── google_search.py
│       │   └── web_content_fetch.py
│       └── weather/          # 날씨 관련 도구
│           └── open_weather_map.py
├── utils/                    # 유틸리티 함수
│   └── rate_limiter.py       # API Rate Limiting 유틸
└── volumes/                  # Docker 볼륨 데이터 (gitignore)
    ├── etcd/                 # etcd 데이터
    ├── milvus/               # Milvus 데이터
    └── minio/                # MinIO 데이터
```

### 디렉토리 설명

-   **`agents/`**: FastAgent 서버의 인스턴스를 생성하고 LLM 모델 설정을 관리합니다.
-   **`db/`**: Milvus와 Oracle DB의 초기 데이터 설정 및 스키마 관리를 담당합니다.
-   **`mcp_servers/config/`**: MCP 서버의 환경 변수 및 설정을 관리합니다.
-   **`mcp_servers/db/`**: Oracle DB 연결 풀 관리 로직이 포함됩니다.
-   **`mcp_servers/tools/`**: FastMCP가 제공하는 도구들을 정의합니다.
    -   **`query/`**: 데이터베이스 쿼리 도구 (Milvus 벡터 검색, Oracle SQL 실행)
    -   **`search/`**: 웹 검색 도구 (Google, DuckDuckGo, 웹 페이지 파싱)
    -   **`weather/`**: 날씨 정보 조회 도구
-   **`utils/`**: Rate Limiting 등 공통 유틸리티 기능이 포함됩니다.
-   **`volumes/`**: Docker 컨테이너의 영구 데이터 저장소입니다. (Git에서 제외됨)

## 🚀 개발 환경 설정

### 1. Python 버전 확인

프로젝트는 Python `3.13` 버전 이상이 필요합니다.

```bash
python --version
```

### 2. 가상 환경 생성 및 활성화

`uv`를 사용하여 가상 환경을 생성하고 활성화합니다.

```bash
# 가상 환경 생성
uv venv

# 가상 환경 활성화 (macOS/Linux)
source .venv/bin/activate

# 가상 환경 활성화 (Windows)
.venv\\Scripts\\activate
```

### 3. 의존성 설치

`uv`를 사용하여 `pyproject.toml`에 명시된 의존성을 설치합니다.

```bash
uv sync
```

### 4. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, 필요한 API 키와 설정을 입력합니다.

```bash
cp .env.example .env
```

그 다음, 선호하는 편집기를 사용하여 `.env` 파일을 열고 각 서비스에 맞는 API 키를 설정합니다.

```dotenv
# .env

`agents` 폴더 아래 `fastagent.secrets.yaml`을 생성하고 아래와 같이 입력합니다.
사용하고자 하는 API 키를 설정합니다.
```

# Google Gemini

# google:

# api_key: ""

# OpenAI:

# api_key: ""

```


# [Tool] DuckDuckGo
DUCKDUCKGO_BASE_URL=https://html.duckduckgo.com/html

# [Tool] WebSearch API
GOOGLE_WEB_SEARCH_URL=https://www.googleapis.com/customsearch/v1
GOOGLE_WEB_SEARCH_API_KEY=YOUR_GOOGLE_SEARCH_API_KEY

# [Tool] OpenWeatherMap API Key
OPEN_WEATHER_MAP_URL=http://api.openweathermap.org/data/2.5/weather
OPEN_WEATHER_MAP_API_KEY=YOUR_OPENWEATHERMAP_API_KEY
```

## ▶️ 서버 실행

다음 명령어를 사용하여 Agent 서버와 FastAPI 서버를 실행합니다. 서버는 기본적으로 `9090, 9092` 포트에서 실행됩니다.

### DB 초기 데이터 설정

```bash
uvicorn db.db_server:app --host 0.0.0.0 --port 9093
```

### Agent 서버 실행

```bash
cd agents
uv run agent_server.py --transport http --port 9090
```

### MCP 서버 실행

```bash
fastmcp run mcp_server.py:mcp --transport http --port 9092
```

### MCP 서버 Inspector 실행 (선택)

npx @modelcontextprotocol/inspector mcp서버실행명령어

```bash
npx @modelcontextprotocol/inspector fastmcp run mcp_server.py:mcp --transport http --port 9092
```

## 🛠️ 등록된 도구

이 서버는 다음과 같은 도구들을 제공합니다:

-   **Google Search**: 구글을 통해 웹 검색을 수행합니다. (구현)
-   **OpenWeatherMap**: 특정 위치의 현재 날씨 정보를 조회합니다. (구현)
-   **WebContentFetcher**: 주어진 URL의 웹 페이지 콘텐츠를 가져와 파싱합니다. (미구현)
-   **DuckDuckGo Search**: DuckDuckGo를 사용하여 웹 검색을 수행합니다. (미구현)

## Milvus 관리 페이지 접속

### Milvus Attu

`http://localhost:8000/` 접속
`milvus address`에 `http://milvus-standalone:19530`을 입력한 후, connect를 클릭합니다.

### Milvus Webui

`http://localhost:9091/webui/` 접속

## 참조

-   **Milvus**: https://milvus.io/docs/configure-docker.md?tab=component
