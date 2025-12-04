import json
from bs4 import BeautifulSoup
from mcp_servers.config.settings import DUCKDUCKGO_BASE_URL
from dataclasses import dataclass
from typing import List
from utils.rate_limiter import RateLimiter
import httpx
import sys
import traceback
import urllib.parse
from mcp.types import TextContent
from fastmcp.tools.tool import ToolResult

"""
==================================================
도구 모듈: DuckDuckGo 비동기 검색기 (DuckDuckGoSearcher)
==================================================
이 파일은 FastMCP 도구로 사용되는 비동기 웹 검색 기능을 제공하는 클래스를 정의합니다.

주요 역할:
1. DuckDuckGo의 HTML 페이지를 스크레이핑하여 검색 결과를 가져옵니다.
2. 봇 감지 회피를 위한 속도 제한(Rate Limiter) 기능을 포함합니다.
3. 검색 결과를 LLM이 처리하기 쉬운 문자열 형태로 변환하는 기능을 제공합니다.
"""

@dataclass
class SearchResult:
    # 단일 검색 결과를 저장하는 데이터 클래스.
    title: str
    link: str
    snippet: str
    position: int


class DuckDuckGoSearcher:
    """
    DuckDuckGo의 HTML 페이지를 스크레이핑하여 검색 결과를 비동기적으로 가져오는 클래스입니다.
    """

    BASE_URL = DUCKDUCKGO_BASE_URL
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self):
        # 인스턴스 초기화 시 속도 제한(Rate Limiter) 객체 생성.
        self.rate_limiter = RateLimiter()

    async def duckduckgo_search(
        self, query: str, max_results: int = 1
    ) -> List[SearchResult]:
        """
        DuckDuckGo 검색을 실행하고 HTML을 파싱하여 결과를 반환합니다.
        
        Args:
            query (str): 검색할 쿼리 문자열.
            max_results (int): 반환할 최대 결과 수 (기본값 1).

        Returns:
            List[SearchResult]: 파싱된 검색 결과 객체 리스트.
        """

        try:
            # 1. 속도 제한 적용 (봇 감지 방지)
            await self.rate_limiter.acquire()

            # 2. POST 요청에 필요한 데이터 설정
            data = {
                "q": query,
                "b": "",
                "kl": "",
            }

            # ctx 객체를 제거했으므로 로깅 기능을 임시 주석 처리.
            # await ctx.info(f"Searching DuckDuckGo for: {query}")
            
            # 3. 비동기 HTTP 요청 실행
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL, data=data, headers=self.HEADERS, timeout=30.0
                )
                response.raise_for_status()

            # 4. HTML 파싱
            soup = BeautifulSoup(response.text, "html.parser")
            if not soup:
                # ctx 객체를 제거했으므로 로깅 기능을 임시 주석 처리.
                # await ctx.error("Failed to parse HTML response")
                return []

            # 5. 검색 결과 추출
            results = []
            for result in soup.select(".result"):
                title_elem = result.select_one(".result__title")
                if not title_elem:
                    continue

                link_elem = title_elem.find("a")
                if not link_elem:
                    continue

                # 제목 및 링크 요소 추출
                title = link_elem.get_text(strip=True)
                link = link_elem.get("href", "")

                # 유효하지 않거나 광고 링크 스킵
                if not link or not isinstance(link, str) or "y.js" in link:
                    continue

                # DuckDuckGo 리디렉션 URL 정리
                if link.startswith("//duckduckgo.com/l/?uddg="):
                    link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

                # 요약(Snippet) 추출
                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                result = {
                    "toolId": "duckduckgo_search",
                    "title": title,
                    "link": link,
                    "snippet": snippet 
                }

                result_str = json.dumps(result, ensure_ascii=False)

                # if len(results) >= max_results:
                #     break
            # ctx 객체를 제거했으므로 로깅 기능을 임시 주석 처리.
            # await ctx.info(f"Successfully found {len(results)} results")
            if result:
                return ToolResult(
                    content=[TextContent(type="text", text=result_str)],
                    structured_content={"data": "value", "count": 42},
                    meta={"execution_time_ms": 145}
                )
            # return results

        # 6. 예외 처리
        except httpx.TimeoutException:
            # ctx 객체를 제거했으므로 로깅 기능을 임시 주석 처리.
            # await ctx.error("Search request timed out")
            return []
        except httpx.HTTPError as e:
            # ctx 객체를 제거했으므로 로깅 기능을 임시 주석 처리.
            # await ctx.error(f"HTTP error occurred: {str(e)}")
            return []
        except Exception as e:
            # ctx 객체를 제거했으므로 로깅 기능을 임시 주석 처리.
            # await ctx.error(f"Unexpected error during search: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            return []