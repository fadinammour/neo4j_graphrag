import os
from dotenv import load_dotenv

from langchain_neo4j import Neo4jVector, Neo4jGraph
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME") 
CHAT_LLM_NAME = os.getenv("CHAT_LLM_NAME") 

embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
llm = ChatOllama(model=CHAT_LLM_NAME, temperature=0)

vector_index = Neo4jVector.from_existing_graph(
    embeddings,
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    index_name='tasks',
    node_label="Task",
    text_node_properties=['name', 'description', 'status'],
    embedding_node_property='embedding',
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

template = """Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, say that you don't know.

Context:
{context}

Question: {question}

Answer:"""

prompt = ChatPromptTemplate.from_template(template)

rag_chain = (
    {"context": vector_index.as_retriever() | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# query = "How will recommendation service be updated?"
# response = rag_chain.invoke(query)

# print(f"\n--- Final Answer ---\n{response}")

print(f"\n--- Final Answer ---\n{rag_chain.invoke('How many open tickets are there?')}")

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)

number_of_open_tickets = graph.query(
    "MATCH (t:Task {status:'Open'}) RETURN count(*)"
)
print(f"Result of graph query of open tickets: {number_of_open_tickets}")
