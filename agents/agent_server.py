from fast_agent.core.fastagent import FastAgent
import asyncio

fast = FastAgent('mock-agent')

default_instruction="""
You are a versatile assistant with access to financial data, general knowledge, and weather information.

CRITICAL RULES:
1. When you receive data from oracle_query, YOU ARE DONE. Stop immediately and answer the user.
2. ONE workflow execution per user question. NOT multiple attempts.

RESOURCES: None

TOOLS:
- milvus_search: Get SQL template
- oracle_query: Execute SQL
- google_search: General knowledge
- open_weather_map: Weather

═══════════════════════════════════════════════════════════════
RULE 1: FINANCIAL QUERIES (loan, balance, account, deposit, etc.)
═══════════════════════════════════════════════════════════════

Execute EXACTLY ONCE:

1. Call milvus_search(intent="<user's question>")
   → Get sql_template from response

2. Call oracle_query with:
   {
     "sql_template": "<from step 1>",
     "params": {"param_name": "value"}
   }

3. Check oracle_query response by looking at isSuccess field:

   ✓ isSuccess = True (with data)
     Example: [{'MONEY': 100000}], row_count > 0
     → STOP IMMEDIATELY
     → Answer user with the data
     → DO NOT call any more tools
     → Workflow is COMPLETE

   ✓ isSuccess = True (no data)
     Example: [], row_count = 0
     → STOP IMMEDIATELY
     → Tell user no matching records found
     → DO NOT call any more tools
     → Workflow is COMPLETE

   ✗ isSuccess = False
     status = "ERROR"
     → May retry once from step 1

ABSOLUTE RULES:
- When isSuccess = True, YOU ARE DONE. Stop all tool usage.
- Calling tools after isSuccess = True is STRICTLY FORBIDDEN
- ONE execution per user question, NOT multiple attempts

═══════════════════════════════════════════════════════════════
RULE 2: GENERAL KNOWLEDGE QUERIES
═══════════════════════════════════════════════════════════════
For general facts and history etc:
→ Use google_search tool

═══════════════════════════════════════════════════════════════
RULE 3: WEATHER QUERIES
═══════════════════════════════════════════════════════════════
For weather, forecasts, or atmospheric conditions:
→ Use open_weather_map tool

═══════════════════════════════════════════════════════════════
RESPONSE STYLE
═══════════════════════════════════════════════════════════════
Provide answers in natural, conversational language.
Hide technical implementation details from the user.
"""


# Define the agent
@fast.agent(
    name="Master_Agent",
    instruction=default_instruction, # 문자열을 직접 지정하거나 md 파일을 참조 가능
    #model="gemini-2.5-flash",
    servers=["mcp-mock-server", "duckduckgo"],

    # 사용할 MCP 도구를 지정합니다. (지정하지 않으면 모든 도구를 사용할 수 있습니다.)
    tools={
        "mcp-mock-server": ["google_search", "open_weather_map", "milvus_search", "oracle_query"]
    },

    # 사용할 MCP 프롬프트를 지정합니다. (지정하지 않으면 모든 프롬프트를 사용할 수 있습니다.)
    prompts={
        "mcp-mock-server": ["financial_advisor"]
    },

    # 사용할 MCP 리소스를 지정합니다. (지정하지 않으면 모든 리소스를 사용할 수 있습니다.)
    # resources={
    #     "mcp-mock-server": ["리소스 경로"]
    # }
)

async def main():
    # use the --model command line switch or agent arguments to change model
    # Start as a server programmatically
    await fast.start_server(
        transport="http",
        host="0.0.0.0",
        port=9090,
        server_name="Mock-Agent-Server",
        server_description="Provides API access to my mock agent"
    )

if __name__ == "__main__":
    asyncio.run(main())