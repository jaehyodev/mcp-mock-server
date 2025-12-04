import json
from mcp_servers.config.settings import GOOGLE_SEARCH_URL, GOOGLE_SEARCH_API_KEY
import requests
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

"""
==================================================
도구 모듈: Google 검색 도구 함수 (google_search)
==================================================
이 파일은 FastMCP 도구로 사용되는 Google Custom Search API 연동 함수를 정의합니다.

주요 역할:
1. Google Custom Search API를 호출하여 웹 검색 결과를 가져옵니다.
2. 검색 결과를 `main_handler`를 통해 LLM에게 전달하여 최종 답변을 생성하도록 위임합니다.
"""

async def google_search(inputs: dict):
    """
    Google Custom Search API를 사용하여 웹 검색을 수행하고, 
    결과를 LLM이 처리하여 자연스러운 답변을 생성합니다.
    
    Args:
        inputs (dict): FastMCP로부터 전달받은 인자 딕셔너리.
                       필수 키: "query", 선택 키: "maxResults".

    Returns:
        dict: LLM이 생성한 최종 응답 또는 에러 메시지를 포함하는 딕셔너리.
    """

    # 1. 입력값 추출
    query = inputs.get("query", "") # 사용자 질문 추출
    max_results = inputs.get("maxResults", 1) # 응답은 1개만 추출

    # 2. Google Custom Search API 호출
    # - 웹 검색 요청을 생성하고, API 키와 쿼리 매개변수를 함께 전달합니다.
    response = requests.get(
        GOOGLE_SEARCH_URL,
        params={"key": GOOGLE_SEARCH_API_KEY, "cx": "47cbc5d656f2b4732", "q": query}
    )

    # 3. 응답 처리 및 데이터 추출
    data = response.json()
    items = data.get("items", [])[:max_results]

    # 4. 결과 반환
    if items:
        result = (
            f"title:{items[0]['title']}, "
            f"link:{items[0]['link']}, "
            f"snippet:{items[0]['snippet']}"
        )
        return ToolResult(
            content=[TextContent(type="text", text=result)],
            structured_content={
                "title": items[0]['title'],
                "link":{items[0]['link']},
                "snippet":{items[0]['snippet']}
            }
        )

    # 5. 검색 실패 처리
    return {
        "error": "Google Search API Call Failed",
        "message": f"검색 실패 → {data.get('message')}"
    }
