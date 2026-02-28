import os
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# NATIVE FIX: Pass FastMCP configuration securely through docker exec flags
# - FASTMCP_LOG_LEVEL=WARNING cleanly disables the ASCII banner and info logs
# - FASTMCP_STATELESS_HTTP=1 strictly satisfies the FastMCP 2.x/3.x deprecation requirement
server_params = StdioServerParameters(
    command="docker",
    args=[
        "exec", "-i", 
        "-e", "FASTMCP_LOG_LEVEL=WARNING", 
        "-e", "FASTMCP_STATELESS_HTTP=1", 
        "mcp_server", 
        "/usr/local/bin/run-mcp.sh"
    ],
    env=os.environ
)

SYSTEM_PROMPT = """You are a Neo4j Graph Database Expert. Answer the user's questions by querying the database.

CRITICAL GRAPH RAG RULES:
1. CHECK SCHEMA: Use 'get_neo4j_schema' to understand the graph structure before writing queries.
2. MAPPING CONCEPTS:
   - "Tickets" or "Tasks" refer to the `Task` node label.
   - "Services" refer to the `Microservice` node label.
3. CASE SENSITIVITY: Always use `toLower()` for string matching. 
   - Example: WHERE toLower(t.status) = 'open'
4. INDIRECT DEPENDENCIES: If asked for 'indirect' dependencies, use variable-length path queries.
   - Example: MATCH (m:Microservice)-[:DEPENDS_ON*2..]->(d:Dependency)
5. RETURN VALUES: Ensure your Cypher query returns the actual properties needed (e.g., RETURN m.name, count(t)).
"""

async def main(questions):
    llm = ChatOllama(model=os.getenv("CHAT_LLM_NAME"), temperature=0)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await load_mcp_tools(session)

            agent = create_react_agent(llm, tools)
            
            for q in questions:
                print(f"\n{'='*60}")
                print(f"Question: {q}")
                print(f"{'='*60}")
                
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=q)
                ]
                
                async for event in agent.astream({"messages": messages}):
                    for node, values in event.items():
                        if node == "agent":
                            message = values["messages"][-1]
                            if message.tool_calls:
                                for tc in message.tool_calls:
                                    query_arg = tc['args'].get('query', 'Fetching Schema...')
                                    print(f"🤖 Tool: {tc['name']}\n   Query: {query_arg}")
                        elif node == "tools":
                            print(f"🛠️  Execution complete.")
                
                final_message = values["messages"][-1]
                print(f"\n✅ Answer:\n{final_message.content}")

if __name__ == "__main__":
    questions = [
        "How many open tickets there are?",
        "How many open tickets there are assigned to TeamA?",
        "Which team has the most open tasks?",
        "Which services depend on Database directly?",
        "Which services depend on Database indirectly?"
    ]
    asyncio.run(main(questions))