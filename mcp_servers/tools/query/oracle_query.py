from mcp.server.fastmcp import Context
from mcp import ServerSession
from db.oracle_init import get_db_connection
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
import oracledb
from fastmcp.dependencies import CurrentContext

from mcp_servers.types import AppContext

async def oracle_query(inputs: dict, ctx: Context = CurrentContext()) -> ToolResult: 
    """
    Milvus에서 선택된 Prepared SQL 템플릿을 실행하는 Oracle 전용 실행 도구
    """
    # 1. lifespan에서 관리되는 pool 가져오기
    pool = ctx.request_context.lifespan_context.oracle.pool
    original_query = inputs.get("original_query", "")
    sql_template = inputs.get("sql_template", "").strip()
    print('[Tool] oracle_query: sql_template >> ', sql_template)
    # 에이전트가 'params' 또는 'parameters' 둘 다 보낼 수 있으므로 양쪽 모두 처리
    parameters = inputs.get("params") or inputs.get("parameters", {})
    print('[Tool] oracle_query: parameters >> ', parameters)

    # SELECT 쿼리만 허용합니다.
    # if not sql_template.upper().startswith("SELECT"):
    #     return ToolResult(
    #         content=[TextContent(type="text", text="SELECT 금지")],
    #         meta={"status": "DENIED"}
    #     )

    if not sql_template:
        return ToolResult(
            content=[TextContent(type="text", text="실행할 SQL 템플릿이 없습니다.")],
            meta={"status": "ERROR"}
        )
    
    query_results = []

    try:
        # 2. 수동 connection 생성 대신 pool에서 빌려오기 (async with 사용)
        async with pool.acquire() as connection:
            print(f"[Tool] oracle_query: Acquired connection from pool: {connection}")

            # 3. cursor 역시 async with로 생성
            async with connection.cursor() as cursor:
                # 비동기 SQL 실행
                await cursor.execute(sql_template, parameters)

                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()

                for row in rows:
                    query_results.append(dict(zip(columns, row)))

    except oracledb.Error as e:
        error_message = f"Oracle DB 쿼리 실행 에러: {e}"
        print(f"[Tool] oracle_query: ❌ 쿼리 실행 에러 → {error_message}")
        return ToolResult(
            content=[TextContent(type="text", text="쿼리 실행 중 오류가 발생했습니다.")],
            structured_content={
                "isSuccess": False,
                "error": error_message
            },
            meta={
                "isSuccess": False,
                "status": "ERROR"
            }
        )
    # async with가 끝나면 connection은 자동으로 pool에 반납됩니다.
        
    if query_results:
        return ToolResult(
            content=[TextContent(type="text", text=str(query_results))],
            structured_content={
                "isSuccess": True,
                "query_result": query_results,
                "sql_template": sql_template,
                "parameters": parameters
            },
            meta={
                "isSuccess": True,
                "row_count": len(query_results),
                "status": "SUCCESS"
            }
        )
    else:
        print(f'[DB - Oracle] 쿼리 결과가 없습니다: {original_query}')
        return  ToolResult(
            content=[TextContent(type="text", text=f"쿼리 '{original_query}'에 대한 결과가 없습니다.")],
            structured_content={
                "isSuccess": True,
                "query_result": [],
                "message": "No matching records found"
            },
            meta={
                "isSuccess": True,
                "row_count": 0,
                "status": "SUCCESS_NO_DATA"
            }
        )
