from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient
from transformers import pipeline

from backend.core.config import get_settings
from backend.rag.embeddings import EmbeddingModel
from backend.rag.reranker import CrossEncoderReranker


@lru_cache(maxsize=2)
def get_embedder() -> EmbeddingModel:
    settings = get_settings()
    return EmbeddingModel(model_name=settings.embedding_model)


@lru_cache(maxsize=2)
def get_reranker() -> CrossEncoderReranker:
    settings = get_settings()
    return CrossEncoderReranker(model_name=settings.reranker_model)


@lru_cache(maxsize=2)
def get_nli_pipeline():
    settings = get_settings()
    return pipeline("text-classification", model=settings.nli_model, truncation=True, top_k=None)


@lru_cache(maxsize=2)
def get_zero_shot_pipeline():
    settings = get_settings()
    return pipeline("zero-shot-classification", model=settings.zero_shot_model)


@lru_cache(maxsize=2)
def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    if not settings.qdrant_api_key:
        raise RuntimeError("QDRANT_API_KEY is not configured in backend/.env")
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
