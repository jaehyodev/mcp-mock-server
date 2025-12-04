from fast_agent.core.fastagent import FastAgent
import asyncio

fast = FastAgent('My awesome agent')

default_instruction=""

# Define the agent
@fast.agent(
    name="Agent_Search",
    instruction=default_instruction, # 문자열을 직접 지정하거나 md 파일을 참조 가능
    #model="gemini-2.5-flash",
    servers=["mcp-mock-server", "duckduckgo"],

    # Filter some of the MCP resources avalable to the agent
    tools={
        "mcp-mock-server": ["google_search", "fetch_and_parse", "open_weather_map"]
    }
)
async def main():
    # use the --model command line switch or agent arguments to change model
    # Start as a server programmatically
    await fast.start_server(
        transport="http",
        host="0.0.0.0",
        port=9090,
        server_name="API-Agent-Server",
        server_description="Provides API access to my agent"
    )

if __name__ == "__main__":
    asyncio.run(main())