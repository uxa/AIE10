"""Advanced Activity: local-model RAG pipeline via Ollama.

Rebuilds the same retrieve-then-generate RAG pipeline as `app/rag.py`, but
with both the chat model and the embedding model running locally through
Ollama instead of Fireworks AI. This lets you compare quality/latency of a
fully local setup against the hosted Fireworks endpoint.

Defaults:
- Chat model:      llama3.2       (override with OLLAMA_CHAT_MODEL)
- Embedding model: nomic-embed-text (override with OLLAMA_EMBEDDING_MODEL)

Prerequisites:
    brew install ollama
    ollama serve                      # in a separate terminal
    ollama pull llama3.2
    ollama pull nomic-embed-text

Usage:
    uv run python -m app.local_rag "What vaccinations do kittens need?"
"""

from __future__ import annotations

import os
import sys
import time
from functools import lru_cache
from typing import Annotated, TypedDict

import tiktoken
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langgraph.graph import START, StateGraph

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_CHAT_MODEL = "llama3.2"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"


def _tiktoken_len(text: str) -> int:
    return len(tiktoken.encoding_for_model("gpt-4o").encode(text))


class _RAGState(TypedDict):
    question: str
    context: list[Document]
    response: str


def _build_local_rag_graph(data_dir: str):
    try:
        documents = DirectoryLoader(
            data_dir, glob="**/*.pdf", loader_cls=PyMuPDFLoader
        ).load()
    except Exception:
        documents = []

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=750, chunk_overlap=0, length_function=_tiktoken_len
    )
    chunks = text_splitter.split_documents(documents) if documents else []

    base_url = os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    embedding_model = OllamaEmbeddings(
        model=os.environ.get("OLLAMA_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        base_url=base_url,
    )
    qdrant_vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_model,
        location=":memory:",
        collection_name="local_rag_collection",
    )
    retriever = qdrant_vectorstore.as_retriever()

    human_template = (
        "\n#CONTEXT:\n{context}\n\nQUERY:\n{query}\n\n"
        "Use the provided context to answer the provided user query. "
        "Only use the provided context to answer the query. If you do not "
        'know the answer, or it is not contained in the provided context, '
        'respond with "I don\'t know"'
    )
    chat_prompt = ChatPromptTemplate.from_messages([("human", human_template)])
    generator_llm = ChatOllama(
        model=os.environ.get("OLLAMA_CHAT_MODEL", DEFAULT_CHAT_MODEL),
        base_url=base_url,
    )

    def retrieve(state: _RAGState) -> _RAGState:
        retrieved_docs = retriever.invoke(state["question"]) if retriever else []
        return {"context": retrieved_docs}  # type: ignore

    def generate(state: _RAGState) -> _RAGState:
        generator_chain = chat_prompt | generator_llm | StrOutputParser()
        response_text = generator_chain.invoke(
            {"query": state["question"], "context": state.get("context", [])}
        )
        return {"response": response_text}  # type: ignore

    graph_builder = StateGraph(_RAGState)
    graph_builder = graph_builder.add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    return graph_builder.compile()


@lru_cache(maxsize=1)
def _get_local_rag_graph():
    data_dir = os.environ.get("RAG_DATA_DIR", "data")
    return _build_local_rag_graph(data_dir)


@tool
def retrieve_information_local(
    query: Annotated[str, "query to ask the local retrieve information tool"],
):
    """Use a fully local (Ollama) Retrieval Augmented Generation pipeline to
    retrieve information about feline health."""
    graph = _get_local_rag_graph()
    result = graph.invoke({"question": query})
    if isinstance(result, dict) and "response" in result:
        return result["response"]
    return result


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()

    question = " ".join(sys.argv[1:]) or "What vaccinations do kittens need?"
    graph = _get_local_rag_graph()

    start = time.perf_counter()
    result = graph.invoke({"question": question})
    elapsed = time.perf_counter() - start

    print(f"Question: {question}")
    print(f"Answer: {result.get('response')}")
    print(f"Latency: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
