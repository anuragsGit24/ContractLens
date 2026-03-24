from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np

from backend.services.model_singleton import embed, embed_single

from .retriever import RetrievedDoc


DEFAULT_RERANKER_MODEL = "law-ai/InLegalBERT"


@dataclass
class RerankedDoc:
    doc: RetrievedDoc
    rerank_score: float


@dataclass
class CrossEncoderReranker:
    model_name: str = DEFAULT_RERANKER_MODEL

    def __post_init__(self) -> None:
        # Compatibility no-op: kept for existing call sites.
        _ = self.model_name

    def rerank(self, query: str, docs: Sequence[RetrievedDoc], top_k: int = 3) -> List[RerankedDoc]:
        if not docs:
            return []

        query_vec = embed_single(query)
        doc_vecs = embed([d.text[:512] for d in docs])
        scores = np.dot(doc_vecs, query_vec)

        reranked = [
            RerankedDoc(doc=docs[i], rerank_score=float(scores[i])) for i in range(len(docs))
        ]
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)
        return reranked[:top_k]
