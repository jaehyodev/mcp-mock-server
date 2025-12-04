# MCP Mock Server

이 프로젝트는 `FastMCP, FastAgent` 프레임워크를 사용하여 구축된 Mock 서버입니다. 다양한 외부 도구(검색, 날씨 등)를 통합하여 API 형태로 제공합니다.

## 🤖 프로젝트 정보

-   **프로젝트 이름**: mcp-mock-server
-   **Python 버전**: 3.13+
-   **주요 프레임워크**: FastAPI, FastMCP, FastAgent

## 📂 프로젝트 구조 (수정 필요)

```
/
├── .env.example              # 환경 변수 예제 파일
├── main.py                   # FastAPI 애플리케이션 실행 파일
├── pyproject.toml            # 프로젝트 의존성 및 설정 파일
├── README.md                 # 프로젝트 설명 파일
├── config/                   # 환경 변수 등 설정 관련 파일
│   └── settings.py
├── mcp_server/               # FastMCP 서버 설정 및 핸들러
│   ├── handlers.py
│   └── server.py
├── resources/                # 서버 리소스 관련 파일
│   └── app_status.py
├── services/                 # 외부 서비스 연동 관련 로직
│   ├── gemini.py
│   └── post_processor.py
├── tools/                    # FastMCP에 등록될 도구들
│   ├── search/               # 검색 관련 도구
│   └── weather/              # 날씨 관련 도구
└── utils/                    # 유틸리티 함수
    └── rate_limiter.py
```

-   **`config`**: 애플리케이션의 설정을 관리합니다. (예: CORS 설정, 환경 변수 로딩)
-   **`mcp_server`**: `FastMCP` 서버의 인스턴스를 생성하고 도구를 등록하는 핵심 로직이 포함됩니다.
-   **`resources`**: 서버의 상태 정보와 같은 내부 리소스를 정의합니다.
-   **`services`**: Gemini API 연동과 같이 비즈니스 로직을 처리하는 서비스가 위치합니다.
-   **`tools`**: `FastMCP`가 사용할 수 있는 도구들(예: 웹 검색, 날씨 조회)을 정의합니다.
-   **`utils`**: 속도 제한과 같은 공통 유틸리티 기능이 포함됩니다.

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

다음 명령어를 사용하여 Agent 서버와 FastAPI 서버를 실행합니다. 서버는 기본적으로 `9090, 9091` 포트에서 실행됩니다.

### Agent 서버 실행

```bash
cd agents
uv run agent.py --transport http --port 9090
```

### FastAPI 서버 실행

```bash
fastmcp run server.py:mcp --transport http --port 9091
```

## 🛠️ 등록된 도구

이 서버는 다음과 같은 도구들을 제공합니다:

-   **Google Search**: 구글을 통해 웹 검색을 수행합니다. (구현)
-   **OpenWeatherMap**: 특정 위치의 현재 날씨 정보를 조회합니다. (구현)
-   **WebContentFetcher**: 주어진 URL의 웹 페이지 콘텐츠를 가져와 파싱합니다. (미구현)
-   **DuckDuckGo Search**: DuckDuckGo를 사용하여 웹 검색을 수행합니다. (미구현)
