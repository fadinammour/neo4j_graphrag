# GraphRAG tutorial with local Ollama and Neo4J MCP server

The following code is built upon an adaptation of the RAG tutorial code on : https://neo4j.com/blog/developer/rag-tutorial/

Changes:
- fixed broken link
- fixed dataset number of open issues (added one open issue)
- adapted code from OpenAI to Ollama
- added local Neo4J MCP server

## Preliminary steps:

1. Make a copy of `.env.template` and `neo4j_auth.template.txt` and name them respectively `.env` and `neo4j_auth.txt`. Replace `<NEO4J_PASSWORD>` with a password of your choice.

2. Install [ollama](https://ollama.com/download) in your CLI then run the following commands to get the required models:
```bash
ollama pull qwen3:30b
ollama pull mxbai-embed-large
```
> Models with fewer paramters are not reliable (Cypher command hallucination and problematic reasonning limitation)

3. Install [Docker Engine](https://docs.docker.com/engine/install/)

4. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Set up Neo4J server and database

1. To set the Neo4J server run:
```bash
docker compose build
docker compose up -d
```

2. Set up environment
```bash
uv sync
```

3. Create the MircroServices database
```bash
uv run python create_graph.py
```

> To check that the server and the database are correctly set up, open the following link in your browser [http://localhost:7474/browser/](http://localhost:7474/browser/)

## Steps to run tutorial:


1. Run 
```bash
uv run python create_graph.py
```

## Useful Neo4J commands 
- Delete entire database
```cypher
MATCH (n)
DETACH DELETE n
````

- Add a user to Neo4J
```cypher
CREATE USER myuser SET PASSWORD 'mypassword' CHANGE NOT REQUIRED;
GRANT ROLE admin TO myuser;
```