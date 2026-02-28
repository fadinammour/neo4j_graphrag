import os
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

graph.refresh_schema()

CHAT_LLM_NAME = os.getenv("CHAT_LLM_NAME") 
CYPHER_LLM_NAME = os.getenv("CYPHER_LLM_NAME")

cypher_llm = ChatOllama(model=CYPHER_LLM_NAME, temperature=0)
qa_llm = ChatOllama(model=CHAT_LLM_NAME, temperature=0)

cypher_chain = GraphCypherQAChain.from_llm(
    cypher_llm=cypher_llm,
    qa_llm=qa_llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True
)

response = cypher_chain.invoke({"query": "How many open tickets are assigned to TeamA?"})
print(response["result"])