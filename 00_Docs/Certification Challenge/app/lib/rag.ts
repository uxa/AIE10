import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { OpenAIEmbeddings } from "@langchain/openai";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import type { Document } from "@langchain/core/documents";

const DATA_DIR = path.join(process.cwd(), "data");

// Default chunking strategy: RecursiveCharacterTextSplitter with 1000-char
// chunks and 150-char overlap. Markdown docs are prose-heavy, so recursive
// splitting on paragraph/sentence boundaries preserves semantic units while
// the overlap keeps cross-boundary context for retrieval.
const CHUNK_SIZE = 1000;
const CHUNK_OVERLAP = 150;

let storePromise: Promise<MemoryVectorStore> | null = null;

async function loadDocuments(): Promise<Document[]> {
  const files = (await readdir(DATA_DIR)).filter((f) => f.endsWith(".md"));
  const splitter = new RecursiveCharacterTextSplitter({
    chunkSize: CHUNK_SIZE,
    chunkOverlap: CHUNK_OVERLAP,
  });

  const docs: Document[] = [];
  for (const file of files) {
    const raw = await readFile(path.join(DATA_DIR, file), "utf-8");
    const chunks = await splitter.createDocuments([raw], [{ source: file }]);
    docs.push(...chunks);
  }
  return docs;
}

// Build (once per warm instance) an in-memory vector index over the bundled
// Airflow/Astronomer docs. Rebuilds on cold start, which is acceptable for a
// small corpus and keeps the app fully serverless-friendly on Vercel.
export async function getVectorStore(): Promise<MemoryVectorStore> {
  if (!storePromise) {
    storePromise = (async () => {
      const docs = await loadDocuments();
      const embeddings = new OpenAIEmbeddings({
        model: "text-embedding-3-small",
      });
      return MemoryVectorStore.fromDocuments(docs, embeddings);
    })();
  }
  return storePromise;
}
