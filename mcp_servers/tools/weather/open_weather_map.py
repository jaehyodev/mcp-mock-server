from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from mcp_servers.config.settings import OPEN_WEATHER_MAP_API_KEY
import requests


"""
==================================================
도구 모듈: OpenWeatherMap 날씨 검색 (open_weather_map)
==================================================
이 파일은 FastMCP 도구로 사용되는 OpenWeatherMap API 연동 함수를 정의합니다.

주요 역할:
1. OpenWeatherMap API를 호출하여 특정 도시의 현재 날씨 정보를 가져옵니다.
2. 검색 결과를 'main_handler'를 통해 LLM에게 전달하여 최종 자연어 답변을 생성하도록 위임합니다.
"""

async def open_weather_map(city: str):
    """
    주어진 도시의 현재 날씨 정보를 OpenWeatherMap API를 통해 가져옵니다.

    Args:
        city (str): 검색할 도시의 이름 (예: Seoul, Busan).

    Returns:
        dict: 도시 이름, 기온, 기상 상태를 포함하는 딕셔너리 또는 에러 메시지.
    """

    # 1. API 키 유효성 검사
    if not OPEN_WEATHER_MAP_API_KEY:
        return {"error": "API Key Required", "message": "날씨 API KEY가 필요합니다."}

    # 2. 요청 매개변수 설정
    params = {
        "q": city,
        "units": "metric",
        "lang": "kr",
        "appid": OPEN_WEATHER_MAP_API_KEY
    }

    # 3. 날씨 API 요청 및 응답 처리 (requests는 동기 방식)
    response = requests.get(
        "http://api.openweathermap.org/data/2.5/weather",
        params=params
    )
    data = response.json()

    # 4. HTTP 상태 코드 확인 및 에러 처리
    if response.status_code != 200:
        return {"error": "Weather API Call Failed", "message": data.get("message")}

    # 5. 응답 데이터 추출 및 반환
    main_data = data.get("main", {})

    # 6. 결과 반환
    result = f"city:{data.get("name")}, temperature:{main_data.get('temp')}°C, condition:{data["weather"][0]["description"]}"
    
    return ToolResult(
        content=[TextContent(type="text", text=result)],
        structured_content={
            "city": data.get("name"), 
            "temperature": data.get("temp"),
            "condition": data["weather"][0]["description"] 
        }
        # meta={"execution_time_ms": 145}
    )

    # 8. 검색 실패 처리
    return {
        "error": "Open Weather Map API Call Failed",
        "message": f"날씨 검색 실패 → {data.get('message')}"
    }
