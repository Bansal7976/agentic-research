# RAG — Retrieval-Augmented Generation

## The problem RAG solves
An LLM only knows its training data. It has never seen YOUR documents (company
PDFs, notes, reports). RAG = fetch the relevant pieces of your documents at
question-time and paste them into the prompt, so the model answers **grounded in
your data** instead of hallucinating.

## The two pipelines (both in [rag-service](../services/rag-service/app/main.py))

**1. Indexing (`POST /upload`)** — happens once per document:
```
PDF/TXT → extract text → split into chunks → embed each chunk → store vectors in Chroma
                                          ↘ raw file archived to Cloud Storage
```
- **Chunking**: `RecursiveCharacterTextSplitter`, 1000 chars with 150 overlap.
  Too big = irrelevant noise in prompts; too small = lost context. Overlap stops
  a sentence being cut in half at a boundary.
- **Embedding**: Gemini's `gemini-embedding-001` turns text into a vector (list of
  numbers) where *similar meaning = nearby vectors*. "EV subsidy" and "electric
  car incentive" land close together even with zero shared words.
- **Vector store**: Chroma persists these vectors on disk (`chroma_db/`) and can
  find nearest neighbors fast. (Production alternatives: pgvector, Vertex AI
  Vector Search, Pinecone — same concept.)

**2. Retrieval (`POST /retrieve`)** — happens on every query:
```
query → embed query → similarity search → top-k chunks + their source filenames
```

## How the agent uses it
The researcher agent has a `search_uploaded_docs` tool
([graph.py](../services/agent-service/app/graph.py)) that calls
`rag-service /retrieve` over HTTP — our first real **microservice-to-microservice**
call. If you've uploaded documents about the topic, the agent mixes your private
knowledge with web research.

## Try it
```bash
curl -F "file=@mynotes.pdf" http://localhost:8001/upload
curl -X POST http://localhost:8001/retrieve -H "Content-Type: application/json" \
     -d '{"query": "what does the report say about revenue", "k": 3}'
```

## What breaks without it
Ask the agent about a private document and it will confidently invent an answer.
RAG replaces "sounds plausible" with "quoted from your file, with the source name".
