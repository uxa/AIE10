# Airflow Docs Copilot

**Live demo:** https://aie10challenge.vercel.app/

An end-to-end **Agentic RAG** application that answers Apache Airflow &
Astronomer questions by retrieving from a bundled documentation knowledge base
and falling back to live web search. Built with Next.js (App Router) +
LangGraph.js, deployable to Vercel, and usable in any phone or laptop browser.

## Stack

| Layer | Choice |
| --- | --- |
| LLM gateway | OpenAI (`gpt-4o-mini`) |
| Orchestration | LangGraph.js `createReactAgent` |
| Tools | `search_airflow_docs` (RAG) + Tavily web search |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector store | In-memory (`MemoryVectorStore`), built from `data/*.md` |
| Memory | LangGraph `MemorySaver` checkpointer, keyed by `thread_id` |
| UI | Next.js 15 + React 19 + Tailwind v4 + lucide-react |
| Evals | LLM-as-judge harness (`evals/run_evals.ts`) |
| Deploy | Vercel |

## Local development

```bash
cp .env.example .env.local   # fill in OPENAI_API_KEY and TAVILY_API_KEY
npm install --legacy-peer-deps
npm run dev                  # http://localhost:3000
```

> Node is at `/opt/homebrew/bin`; if `node`/`npm` aren't on your PATH, prefix
> commands with `export PATH="/opt/homebrew/bin:$PATH";`.

## Environment variables

| Var | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | yes | LLM + embeddings |
| `TAVILY_API_KEY` | yes | agentic web search tool |
| `OPENAI_MODEL` | no | chat model, default `gpt-4o-mini` |
| `RETRIEVER_MODE` | no | `naive` or `multiquery` (default `multiquery`) |

## Evaluation

```bash
npm run eval    # scores naive vs multiquery retrievers with an LLM judge
```

Outputs a comparison table (avg correctness, grounded rate, latency) and saves
JSON to `evals/results/`.

## Deploy to Vercel

Set the framework to Next.js, add the env vars above, and deploy. The `data/`
folder is bundled into the `/api/chat` serverless function via
`outputFileTracingIncludes`.
