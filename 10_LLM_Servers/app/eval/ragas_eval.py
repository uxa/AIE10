"""Activity 1: RAGAS evaluation with cost analysis.

Builds two equivalent RAG pipelines over the same cat-health PDF corpus:

- "fireworks": open-source `gpt-oss-20b` generation + `qwen3-embedding-8b`
  embeddings, both served via Fireworks AI.
- "openai": `gpt-4.1-mini` generation + `text-embedding-3-small` embeddings.

Each pipeline answers a small fixed evaluation set, RAGAS scores faithfulness,
answer relevancy, context precision, and context recall for both, and a
rough per-query cost estimate (using each provider's published per-token
pricing and the token usage reported on each response) is printed alongside
the RAGAS scores.

Both pipelines are also tagged for LangSmith so that, when
`LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` are set, each run shows up
in the LangSmith dashboard tagged by provider for further cost/latency
inspection.

Usage:
    uv run python -m app.eval.ragas_eval
"""

from __future__ import annotations

import os
import sys
import types
from dataclasses import dataclass, field
from typing import Literal

import tiktoken
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"

Provider = Literal["fireworks", "openai"]

# Approximate published per-million-token pricing (USD). Update as pricing
# changes; this is only meant to give a directionally correct cost comparison.
PRICING_PER_MILLION_TOKENS = {
    "fireworks": {"input": 0.20, "output": 0.20},  # gpt-oss-20b
    "openai": {"input": 0.40, "output": 1.60},  # gpt-4.1-mini
}

HUMAN_TEMPLATE = (
    "\n#CONTEXT:\n{context}\n\nQUERY:\n{query}\n\n"
    "Use the provided context to answer the provided user query. "
    "Only use the provided context to answer the query. If you do not know "
    'the answer, or it is not contained in the provided context, respond '
    'with "I don\'t know"'
)

EVAL_DATASET = [
    {
        "question": "How often should kittens be dewormed?",
        "ground_truth": (
            "Kittens should typically be dewormed every two weeks starting "
            "at two to three weeks of age until they are about eight to "
            "twelve weeks old, then monthly until six months of age."
        ),
    },
    {
        "question": "What core vaccinations do kittens need?",
        "ground_truth": (
            "Core kitten vaccinations typically include FVRCP (feline "
            "viral rhinotracheitis, calicivirus, panleukopenia) and rabies."
        ),
    },
    {
        "question": "What are common signs of feline dehydration?",
        "ground_truth": (
            "Common signs of dehydration in cats include lethargy, sunken "
            "eyes, dry or tacky gums, decreased skin elasticity (skin tenting), "
            "and reduced appetite."
        ),
    },
]


def _tiktoken_len(text: str) -> int:
    return len(tiktoken.encoding_for_model("gpt-4o").encode(text))


def _load_chunks(data_dir: str) -> list[Document]:
    try:
        documents = DirectoryLoader(
            data_dir, glob="**/*.pdf", loader_cls=PyMuPDFLoader
        ).load()
    except Exception:
        documents = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=750, chunk_overlap=0, length_function=_tiktoken_len
    )
    return splitter.split_documents(documents) if documents else []


@dataclass
class RagPipeline:
    provider: Provider
    retriever: object
    chain: object
    input_price_per_million: float
    output_price_per_million: float
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def answer(self, question: str) -> dict:
        docs = self.retriever.invoke(question) if self.retriever else []
        response = self.chain.invoke({"query": question, "context": docs})
        usage = getattr(response, "usage_metadata", None) or {}
        self.total_input_tokens += usage.get("input_tokens", 0)
        self.total_output_tokens += usage.get("output_tokens", 0)
        return {
            "answer": response.content,
            "contexts": [doc.page_content for doc in docs],
        }

    def estimated_cost_usd(self) -> float:
        return (
            self.total_input_tokens * self.input_price_per_million / 1_000_000
            + self.total_output_tokens * self.output_price_per_million / 1_000_000
        )


def build_pipeline(provider: Provider, chunks: list[Document]) -> RagPipeline:
    """Build a retrieve-then-generate RAG pipeline for the given provider."""
    if provider == "fireworks":
        embeddings = OpenAIEmbeddings(
            model=os.environ.get(
                "FIREWORKS_EMBEDDING_MODEL",
                "accounts/fireworks/models/qwen3-embedding-8b",
            ),
            openai_api_key=os.environ["FIREWORKS_API_KEY"],
            openai_api_base=FIREWORKS_BASE_URL,
            check_embedding_ctx_length=False,
            dimensions=4096,
        )
        llm = ChatOpenAI(
            model=os.environ.get(
                "FIREWORKS_CHAT_MODEL", "accounts/fireworks/models/gpt-oss-20b"
            ),
            openai_api_key=os.environ["FIREWORKS_API_KEY"],
            openai_api_base=FIREWORKS_BASE_URL,
        ).with_config(tags=["ragas-eval", "provider:fireworks"])
    else:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.environ["OPENAI_API_KEY"],
        )
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            openai_api_key=os.environ["OPENAI_API_KEY"],
        ).with_config(tags=["ragas-eval", "provider:openai"])

    vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        location=":memory:",
        collection_name=f"ragas_eval_{provider}",
    )
    retriever = vectorstore.as_retriever()
    prompt = ChatPromptTemplate.from_messages([("human", HUMAN_TEMPLATE)])
    chain = prompt | llm

    pricing = PRICING_PER_MILLION_TOKENS[provider]
    return RagPipeline(
        provider=provider,
        retriever=retriever,
        chain=chain,
        input_price_per_million=pricing["input"],
        output_price_per_million=pricing["output"],
    )


def _patch_missing_vertexai_shim() -> None:
    """Work around a ragas/langchain-community version mismatch.

    `ragas` unconditionally imports `langchain_community.chat_models.vertexai`,
    but recent `langchain-community` releases (which are being sunset in favor
    of standalone integration packages) removed that module entirely. We never
    use Vertex AI here, so a no-op stub satisfies the import without changing
    any behavior we rely on.
    """
    module_name = "langchain_community.chat_models.vertexai"
    if module_name in sys.modules:
        return
    try:
        __import__(module_name)
        return
    except ModuleNotFoundError:
        stub = types.ModuleType(module_name)

        class ChatVertexAI:  # pragma: no cover - unused stub
            def __init__(self, *args, **kwargs):
                raise NotImplementedError(
                    "ChatVertexAI is unavailable: langchain-community no "
                    "longer ships this integration."
                )

        stub.ChatVertexAI = ChatVertexAI
        sys.modules[module_name] = stub


def run_ragas(provider: Provider, pipeline: RagPipeline) -> dict:
    """Score a pipeline's answers on the eval dataset with RAGAS metrics."""
    _patch_missing_vertexai_shim()
    from ragas import EvaluationDataset, evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    judge_llm = LangchainLLMWrapper(
        ChatOpenAI(model="gpt-4.1-mini", openai_api_key=os.environ["OPENAI_API_KEY"])
    )

    samples = []
    for row in EVAL_DATASET:
        result = pipeline.answer(row["question"])
        samples.append(
            {
                "user_input": row["question"],
                "response": result["answer"],
                "retrieved_contexts": result["contexts"],
                "reference": row["ground_truth"],
            }
        )

    dataset = EvaluationDataset.from_list(samples)
    scores = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=judge_llm,
    )
    return {
        "provider": provider,
        "scores": scores.to_pandas().mean(numeric_only=True).to_dict(),
        "estimated_cost_usd": pipeline.estimated_cost_usd(),
        "input_tokens": pipeline.total_input_tokens,
        "output_tokens": pipeline.total_output_tokens,
    }


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()

    data_dir = os.environ.get("RAG_DATA_DIR", "data")
    chunks = _load_chunks(data_dir)
    if not chunks:
        raise SystemExit(f"No PDF chunks found under '{data_dir}'.")

    results = []
    for provider in ("fireworks", "openai"):
        print(f"\n=== Evaluating provider: {provider} ===")
        pipeline = build_pipeline(provider, chunks)
        results.append(run_ragas(provider, pipeline))

    print("\n=== RAGAS + Cost Comparison ===")
    for r in results:
        print(f"\nProvider: {r['provider']}")
        for metric, value in r["scores"].items():
            print(f"  {metric}: {value:.3f}")
        print(f"  input_tokens: {r['input_tokens']}  output_tokens: {r['output_tokens']}")
        print(f"  estimated_cost_usd: ${r['estimated_cost_usd']:.6f}")


if __name__ == "__main__":
    main()
