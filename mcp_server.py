from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from mcp_servers.config.settings import CORS_ORIGINS
from mcp_servers.db.oracle import OracleManager
from mcp_servers.resources.characters import register_characters_resource
from mcp_servers.types import AppContext
from mcp_servers.tools.query.milvus_search import milvus_search
from mcp_servers.tools.query.oracle_query import oracle_query
from mcp_servers.tools.search.duckduckgo_search import DuckDuckGoSearcher
from mcp_servers.tools.search.google_search import google_search
from mcp_servers.tools.search.web_content_fetch import WebContentFetcher
from mcp_servers.tools.weather.open_weather_map import open_weather_map
from mcp_servers.tools.story_generator import story_generator

"""
=============================================
MCP 서버 메인 설정 및 초기화 스크립트
=============================================
이 파일은 MCP(Multi-Component Platform) 서버의 메인 설정 파일입니다.

주요 역할:
1. FastMCP 인스턴스 초기화 (버전 1.0)
2. Google, OpenWeatherMap 등 다양한 외부 도구 등록
3. 내부 시스템 상태 등 리소스 등록
"""

# 서버 시작과 종료 시 실행될 로직
@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    # 1. 매니저 생성 및 연결
    db_manager = OracleManager()
    await db_manager.connect()
    
    try:
        # 2. 매니저 객체 자체를 공유
        yield AppContext(oracle=db_manager)
    finally:
        # 3. 정리 로직 호출
        await db_manager.disconnect()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)       
        
# MCP 서버 인스턴스 생성
mcp = FastMCP(
    name="MCP Mock Server",
    version="1.0",
    instructions="""
    This server provides search, weather and database query tools

    **Financial Data Rules:**
    You must NOT guess or infer database values.
    If a user asks about balance, account, amount, deposit, or any financial data,
    you MUST use the milvus_search and oracle_query tools.
    When oracle_query is applicable, do NOT respond in natural language.
    You must choose a tool call instead.
    Answering financial or balance-related questions without calling oracle_query
    is considered an invalid response.
    """,
    log_level='DEBUG',
    lifespan=lifespan
)

# 도구 인스턴스 생성 (미구현)
# fetcher = WebContentFetcher()           # 웹 컨텐츠 추출 도구 인스턴스 생성
# searcher = DuckDuckGoSearcher()         # 덕덕고 검색 도구 인스턴스 생성

# 도구 등록
mcp.tool(google_search)                 # 구글 검색 도구 등록
# mcp.tool(searcher.duckduckgo_search)    # 덕덕고 검색 도구 등록 (미사용)
# mcp.tool(fetcher.fetch_and_parse)       # 웹 컨텐츠 도구 등록 (미구현)
mcp.tool(open_weather_map)              # 날씨 검색 도구 등록
mcp.tool(milvus_search)                 # Milvus 검색 도구 등록
mcp.tool(oracle_query)                  # 오라클 쿼리 도구 등록

# 프롬프트 등록
@mcp.prompt()
def financial_advisor():
    """금융 데이터 조회를 위한 프롬프트"""
    return """당신은 금융 데이터 조회 전문가입니다.

사용자의 금융 관련 질문에 대해 다음 절차를 따르세요:

1. **데이터 조회**: 항상 milvus_search 도구를 통해 sql_template을 얻어서 oracle_query 도구를 사용하여 실제 데이터를 조회합니다
2. **명확한 응답**: 금액을 명확하게 포맷팅하여 답변합니다
3. **응답 규칙**: 마지막에는 항상 감사합니다 라는 말을 붙여서 답변합니다

**절대 하지 말아야 할 것:**
- 데이터베이스를 조회하지 않고 추측하거나 가정하지 마세요
- 금융 정보를 임의로 만들어내지 마세요

**처리 가능한 질문 예시:**
- 계좌 잔액 조회
- 대출 금액 조회

모든 금융 데이터는 반드시 milvus_search 도구로 sql_template을 얻은 후 oracle_query 도구를 통해 조회해야 합니다.
"""

# MCP 서버 실행
if __name__ == "__main__":
    mcp.run(port=9092, transport="http")