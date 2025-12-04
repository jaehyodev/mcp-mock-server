from bs4 import BeautifulSoup  
from mcp.server.fastmcp import Context 
from utils.rate_limiter import RateLimiter
import httpx                     
import re                       

"""
==================================================
도구 모듈: 웹 콘텐츠 추출기 (WebContentFetcher)
==================================================
이 파일은 FastMCP 도구로 사용되는 비동기 웹 페이지 콘텐츠 추출 클래스를 정의합니다.

주요 역할:
1. 주어진 URL에서 HTML 콘텐츠를 비동기적으로 가져옵니다.
2. 봇 감지 회피를 위한 속도 제한(Rate Limiter) 기능을 포함합니다.
3. HTML에서 스크립트, 스타일, 네비게이션 요소 등을 제거하고, 텍스트를 추출 및 정제하여 LLM이 처리하기 쉽도록 최적화합니다.
"""

class WebContentFetcher:
    """
    URL을 받아 웹 페이지의 내용을 비동기적으로 가져와 정제된 텍스트를 반환하는 클래스입니다.
    """

    def __init__(self):
        # 인스턴스 초기화 시 속도 제한(Rate Limiter) 객체 생성.
        self.rate_limiter = RateLimiter(requests_per_minute=20)

    async def fetch_and_parse(self, url: str, ctx: Context) -> str:
        """
        주어진 URL에서 콘텐츠를 가져와 파싱하고 텍스트를 정제하여 반환합니다.

        Args:
            url (str): 콘텐츠를 가져올 웹 페이지 주소.
            ctx (Context): FastMCP 런타임 환경 정보 및 로깅 객체.

        Returns:
            str: 정제된 웹 페이지 텍스트 콘텐츠 또는 에러 메시지.
        """

        try:
            # 1. 속도 제한 획득 및 로깅
            await self.rate_limiter.acquire()
            
            await ctx.info(f"Fetching content from: {url}")
            
            # 2. 비동기 HTTP 요청 실행
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True,
                    timeout=30.0,
                )
                response.raise_for_status() # 4xx/5xx 에러 시 예외 발생

            # 3. HTML 파싱
            soup = BeautifulSoup(response.text, "html.parser")

            # 스크립트, 스타일, 네비게이션 등 LLM에게 불필요한 태그 제거 (Decomposition)
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # 4. 텍스트 추출 및 정제
            text = soup.get_text()
            # 텍스트 정제
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            # 정규 표현식을 사용하여 남아있는 과도한 공백 제거
            text = re.sub(r"\s+", " ", text).strip()

            # 5. 길이 제한 (LLM 토큰 수 제한 고려)
            if len(text) > 8000:
                text = text[:8000] + "... [content truncated]"

            await ctx.info(
                f"Successfully fetched and parsed content ({len(text)} characters)"
            )

            return text

        # 6. 예외 처리
        except httpx.TimeoutException:
            await ctx.error(f"Request timed out for URL: {url}")
            return "Error: The request timed out while trying to fetch the webpage."
        except httpx.HTTPError as e:
            await ctx.error(f"HTTP error occurred while fetching {url}: {str(e)}")
            return f"Error: Could not access the webpage ({str(e)})"
        except Exception as e:
            await ctx.error(f"Error fetching content from {url}: {str(e)}")
            return f"Error: An unexpected error occurred while fetching the webpage ({str(e)})"