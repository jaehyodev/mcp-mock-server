from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from httpx import Request
from mcp_servers.config.settings import CORS_ORIGINS
from mcp_servers.tools.query.oracle_query import oracle_query
from mcp_servers.tools.search.duckduckgo_search import DuckDuckGoSearcher
from mcp_servers.tools.search.google_search import google_search
from mcp_servers.tools.search.web_content_fetch import WebContentFetcher
from mcp_servers.tools.weather.open_weather_map import open_weather_map
from mcp_servers.resources.app_status import register_system_status_resource

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
    instructions="This server provides search and weather tools.",
    log_level='DEBUG',
)

# 도구 인스턴스 생성
fetcher = WebContentFetcher()           # 웹 컨텐츠 추출 도구 인스턴스 생성
searcher = DuckDuckGoSearcher()         # 덕덕고 검색 도구 인스턴스 생성

# 도구 등록
mcp.tool(google_search)                 # 구글 검색 도구 등록
mcp.tool(open_weather_map)              # 날씨 검색 도구 등록
mcp.tool(fetcher.fetch_and_parse)       # 웹 컨텐츠 도구 등록 (미구현)
mcp.tool(searcher.duckduckgo_search)    # 덕덕고 검색 도구 등록 (미사용)
mcp.tool(oracle_query)                  # 오라클 쿼리 도구 등록 (미구현)

# # 리소스 등록
register_system_status_resource(mcp)    # 시스템 상태 리소스 등록

# MCP 서버 실행
if __name__ == "__main__":
    mcp.run(port=9090, transport="http")