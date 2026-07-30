# LangChain & Gemini

## The LLM: Gemini
Gemini is Google's LLM, used here via a free API key from
[aistudio.google.com](https://aistudio.google.com). Key ideas:
- **Tokens** — text is processed in chunks (~4 chars each); pricing and limits are
  per token. Our free tier is enough for this project.
- **Temperature** — 0 = deterministic/factual, 1 = creative. We use 0.2–0.3
  because research should be factual ([graph.py](../services/agent-service/app/graph.py) `_llm()`).
- **Context window** — how much text the model can see at once. Why we summarize
  findings before writing the final report.

## What is LangChain?
LangChain is a toolkit that standardizes working with LLMs, so your code isn't
tied to one provider. Swap Gemini for Claude by changing ONE line. We use:

1. **Chat model wrapper**
   ```python
   llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.3)
   msg = await llm.ainvoke("Summarize this ...")
   ```
2. **Structured output** — forcing the LLM to return a typed object instead of
   free text. Our planner MUST return a list of sub-questions, not an essay:
   ```python
   class Plan(BaseModel):
       subquestions: list[str]
   planner_llm = llm.with_structured_output(Plan)
   ```
   Under the hood this uses Gemini's function-calling to guarantee the shape.
3. **Tools** — Python functions the LLM can decide to call
   (`@tool search_uploaded_docs` in graph.py, plus all the MCP tools).
4. **Embeddings** — `GoogleGenerativeAIEmbeddings` in the rag-service (see [doc 03](03-rag.md)).

## Where in our code
- [graph.py](../services/agent-service/app/graph.py) — chat model, structured planner, tools
- [rag-service/app/main.py](../services/rag-service/app/main.py) — embeddings
- [evals/run_evals.py](../evals/run_evals.py) — Gemini as an LLM judge

## What breaks without it
Without LangChain you'd hand-write HTTP calls to Gemini, JSON-parse fragile
outputs yourself, and rewrite everything to try another model. Without structured
output, the planner sometimes returns prose and the whole pipeline crashes.
