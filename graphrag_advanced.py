# # Advanced Graph RAG implementation

# ## Load libraries

import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

# ## Setup Neo4J and Ollama servers

load_dotenv()

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)
graph.refresh_schema()

CHAT_LLM_NAME = os.getenv("CHAT_LLM_NAME") 
CYPHER_LLM_NAME = os.getenv("CYPHER_LLM_NAME")

# ## Initialise Graph RAG chain

cypher_llm = ChatOllama(model=CYPHER_LLM_NAME, temperature=0)
qa_llm = ChatOllama(model=CHAT_LLM_NAME, temperature=0)

# A specific instruction prompt is given for writing robust cypher instructions.

CYPHER_GENERATION_TEMPLATE = """Task: Generate a Cypher query to answer a user's question.
Schema: {schema}
Question: {question}

CRITICAL RULES:
1. Provide ONLY the Cypher query. No preamble, no markdown.
2. Property values are CASE-SENSITIVE. Always use toLower() for string matches.
   - Example: WHERE toLower(t.status) = 'open'
   - Example: WHERE toLower(d.name) = 'database'
3. NO 'GROUP BY': Aggregation is implicit in Cypher. 
4. If the question asks "Which services", return ms.name or service.name.

Cypher:"""

cypher_prompt = PromptTemplate(
    template=CYPHER_GENERATION_TEMPLATE, 
    input_variables=["schema", "question"]
)

# A specific instruction prompt is given for answering questions, mainly how to interpret cypher outputs.

QA_TEMPLATE = """Task: Answer the question using the provided graph database results.

Question: {question}
Context (Database Results): {context}

CRITICAL INSTRUCTIONS:
1. The provided context IS the result of a complex graph traversal. 
2. If names or values are present in the context, they ARE the answer. 
3. Simply list the items found in the context. Do not look for words like "indirectly" or "most" in the context; those were already handled by the database query.
4. If the context contains team names or service names, extract them and provide them in the answer.

Answer:"""

qa_prompt = PromptTemplate(
    template=QA_TEMPLATE, 
    input_variables=["question", "context"]
)

cypher_chain = GraphCypherQAChain.from_llm(
    cypher_llm=cypher_llm,
    qa_llm=qa_llm,
    graph=graph,
    verbose=True,
    cypher_prompt=cypher_prompt,
    qa_prompt=qa_prompt,
    allow_dangerous_requests=True
)

# ## Ask questions

question = "How many open tickets there are?"
print(f"\n--- Question ---\n{question}")
response = cypher_chain.invoke({"query": question})
print(f"Result: {response['result']}")

# Match answer with correct graph query

number_of_open_tickets = graph.query(
    "MATCH (t:Task {status:'Open'}) RETURN count(*)"
)[0]['count(*)']
print(f"Result of graph query of open tickets: {number_of_open_tickets}")

questions = [
    "How many open tickets there are assigned to TeamA??",
    "Which team has the most open tasks?",
    "Which services depend on Database directly?",
    "Which services depend on Database indirectly?"
]

for q in questions:
    print(f"\n--- Question ---\n{q}")
    response = cypher_chain.invoke({"query": q})
    print(f"Result: {response['result']}")
