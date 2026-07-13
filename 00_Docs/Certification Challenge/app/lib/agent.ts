import { ChatOpenAI } from "@langchain/openai";
import { tool } from "@langchain/core/tools";
import { TavilySearchResults } from "@langchain/community/tools/tavily_search";
import { MemorySaver } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { MultiQueryRetriever } from "langchain/retrievers/multi_query";
import type { BaseRetrieverInterface } from "@langchain/core/retrievers";
import { z } from "zod";
import { getVectorStore } from "./rag";

// Retriever mode is switchable for the Task 6 advanced-retriever comparison.
//   naive       -> plain top-k similarity search
//   multiquery  -> LLM expands the query into several variations, unions results
export type RetrieverMode = "naive" | "multiquery";

export const RETRIEVER_MODE: RetrieverMode =
  (process.env.RETRIEVER_MODE as RetrieverMode) || "multiquery";

const TOP_K = 4;

async function buildRetriever(
  mode: RetrieverMode,
  llm: ChatOpenAI,
): Promise<BaseRetrieverInterface> {
  const store = await getVectorStore();
  const base = store.asRetriever({ k: TOP_K });
  if (mode === "multiquery") {
    return MultiQueryRetriever.fromLLM({ llm, retriever: base });
  }
  return base;
}

export async function buildAgent(mode: RetrieverMode = RETRIEVER_MODE) {
  const llm = new ChatOpenAI({
    model: process.env.OPENAI_MODEL || "gpt-4o-mini",
    temperature: 0,
  });

  const retriever = await buildRetriever(mode, llm);

  const retrieveDocs = tool(
    async ({ query }: { query: string }) => {
      const docs = await retriever.invoke(query);
      if (!docs.length) return "No relevant documentation found.";
      return docs
        .map(
          (d, i) =>
            `[Doc ${i + 1} | source: ${d.metadata?.source ?? "unknown"}]\n${d.pageContent}`,
        )
        .join("\n\n---\n\n");
    },
    {
      name: "search_airflow_docs",
      description:
        "Search the internal Apache Airflow & Astronomer documentation knowledge base. Use this FIRST for any question about Airflow concepts, DAGs, operators, scheduling, Astronomer CLI, or configuration.",
      schema: z.object({
        query: z.string().describe("The natural-language search query."),
      }),
    },
  );

  const tools: unknown[] = [retrieveDocs];

  // External agentic search tool (public data) — only enabled when a key exists.
  if (process.env.TAVILY_API_KEY) {
    tools.push(new TavilySearchResults({ maxResults: 3 }));
  }

  const checkpointer = new MemorySaver();

  const systemPrompt = `You are the Airflow Docs Copilot, an expert assistant for Apache Airflow and Astronomer.

Guidelines:
- ALWAYS call \`search_airflow_docs\` first for questions about Airflow/Astronomer concepts.
- Use the Tavily web-search tool only for recent releases, version-specific changes, or when the docs lack an answer.
- Ground every answer in retrieved context and cite the source filename in parentheses.
- If you cannot find an answer, say so plainly instead of guessing.
- Be concise and include short code snippets when helpful.`;

  return createReactAgent({
    llm,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    tools: tools as any,
    checkpointSaver: checkpointer,
    stateModifier: systemPrompt,
  });
}
