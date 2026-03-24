from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient

from .embeddings import DEFAULT_EMBEDDING_MODEL, EmbeddingModel
from .reranker import CrossEncoderReranker
from .retriever import QdrantRetriever, RetrievedDoc


logger = logging.getLogger("contractlens.rag")


def _load_backend_env() -> None:
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=backend_env, override=False)


def _infer_act_filter(query: str) -> Optional[str]:
    q = query.lower()
    if "contract" in q:
        return "contract_act"
    if "ipc" in q or "crime" in q:
        return "ipc"
    return None


@lru_cache(maxsize=4)
def _get_embedder(model_name: str) -> EmbeddingModel:
    return EmbeddingModel(model_name=model_name)


@lru_cache(maxsize=4)
def _get_reranker(model_name: str) -> CrossEncoderReranker:
    return CrossEncoderReranker(model_name=model_name)


@lru_cache(maxsize=4)
def _get_qdrant_client(url: str, api_key: str) -> QdrantClient:
    return QdrantClient(url=url, api_key=api_key)


@lru_cache(maxsize=8)
def _get_retriever(url: str, api_key: str, collection_name: str) -> QdrantRetriever:
    client = _get_qdrant_client(url=url, api_key=api_key)
    return QdrantRetriever(client=client, collection_name=collection_name)


@dataclass
class RetrievalResult:
    query: str
    act_filter: Optional[str]
    raw_top10: List[RetrievedDoc]
    top3: List[RetrievedDoc]


def retrieve_top_sections(query: str, top_k_raw: int = 10, top_k_final: int = 3) -> RetrievalResult:
    _load_backend_env()

    qdrant_url = os.getenv(
        "QDRANT_URL",
        "https://5d12e4e3-03ea-4848-b40c-a1ed6490a4c5.eu-central-1-0.aws.cloud.qdrant.io",
    )
    api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION", "contractlens_legal")

    if not api_key:
        raise RuntimeError("QDRANT_API_KEY not set (backend/.env)")

    embedding_model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    reranker_model_name = os.getenv("RERANKER_MODEL", "law-ai/InLegalBERT")

    embedder = _get_embedder(model_name=embedding_model_name)
    retriever = _get_retriever(url=qdrant_url, api_key=api_key, collection_name=collection_name)
    reranker = _get_reranker(model_name=reranker_model_name)

    act_filter = _infer_act_filter(query)

    logger.debug("Query: %s", query)
    logger.debug("Act filter: %s", act_filter)

    qvec = embedder.embed_query(query)
    raw = retriever.search(query_vector=qvec, limit=top_k_raw, act=act_filter)

    logger.debug("Top %d raw results:", len(raw))
    for i, d in enumerate(raw, start=1):
        logger.debug(
            "%d) score=%.4f act=%s section=%s title=%s id=%s",
            i,
            d.score,
            d.act,
            d.section_number,
            d.payload.get("title"),
            d.id,
        )

    reranked = reranker.rerank(query=query, docs=raw, top_k=top_k_final)
    top3 = [r.doc for r in reranked]

    logger.debug("Top %d after rerank:", len(top3))
    for i, d in enumerate(top3, start=1):
        rerank_score = next((r.rerank_score for r in reranked if r.doc.id == d.id), None)
        logger.debug(
            "%d) rerank=%.4f act=%s section=%s title=%s id=%s",
            i,
            float(rerank_score or 0.0),
            d.act,
            d.section_number,
            d.payload.get("title"),
            d.id,
        )

    return RetrievalResult(query=query, act_filter=act_filter, raw_top10=raw, top3=top3)
