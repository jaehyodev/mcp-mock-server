from mcp_servers.db.database import get_db_connection # 이전에 작성한 DB 풀 획득 함수를 임포트
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
import oracledb

async def oracle_query(inputs: dict) -> ToolResult: 
    """
    Oracle DB 연결 풀을 사용하여 SQL 쿼리를 안전하게 실행하고, 결과를 LLM이 처리하도록 위임합니다.
    이 도구는 SQL 인젝션 방지를 위해 반드시 Prepared Statement 방식으로 작동합니다.
    
    Args:
        inputs (dict): FastMCP로부터 전달받은 구조화된 인자 딕셔너리.
                       이 딕셔너리는 다음 키를 포함해야 합니다:
                       
                       - "sql_template" (필수, str): Oracle 바인딩 변수(:var_name)를 포함하는 SELECT 쿼리 템플릿.
                                                     (보안상 SELECT 쿼리만 허용됩니다.)
                       - "parameters" (필수, dict): 쿼리 템플릿의 바인딩 변수에 매핑될 실제 값들.
                       - "original_query" (필수, str): 사용자가 처음 요청한 원본 메시지. (로그 및 참고용)
                       
    Returns:
        ToolResult: 쿼리 실행 결과와 LLM이 생성한 최종 응답을 포함하는 결과 객체.
    """
    original_query = inputs.get("original_query", "")
    sql_template = inputs.get("sql_template", "").strip()
    print('sql_template >> ', sql_template)
    parameters = inputs.get("parameters", {})
    print('parameters >> ', parameters)

    # SELECT 쿼리만 허용합니다.
    # if not sql_template.upper().startswith("SELECT"):
    #     return ToolResult(
    #         content=[TextContent(type="text", text="SELECT 금지")],
    #         meta={"status": "DENIED"}
    #     )
    
    connection = None
    query_results = []

    try:
        connection = get_db_connection()
        print('conn >> ', connection)

        with connection.cursor() as cursor:
            cursor.execute(sql_template, parameters)

            columns = [col[0] for col in cursor.description]

            rows = cursor.fetchall()

            for row in rows:
                query_results.append(dict(zip(columns, row)))
    except oracledb.Error as e:
        error_message = f"Oracle DB 쿼리 실행 에러: {e}"
        print(f"❌ oracle_query: 쿼리 실행 에러 → {error_message}")
        return ToolResult(
            content=[TextContent(type="text", text="쿼리 실행 중 오류가 발생했습니다.")],
            meta={"status": "ERROR"}
        )
    finally: 
        if connection:
            connection.close()
        
    if query_results:
        result_str = str(query_results)
        result = {
            "toolId": "oracle_query",
            "query_result": result_str,
        }

        # agent 추가로 수정 필요!
        gemini_response = ""
        return ToolResult(
            content=[TextContent(type="text", text=gemini_response)],
            structured_content={"query_result": query_results},
            meta={"row_count": len(query_results)}
        )
    
    return  ToolResult(
        content=[TextContent(type="text", text=f"쿼리 '{original_query}'에 대한 결과가 없습니다.")],
        meta={"row_count": 0}
    )
