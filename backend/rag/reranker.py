from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from sentence_transformers import CrossEncoder

from .retriever import RetrievedDoc


DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@dataclass
class RerankedDoc:
    doc: RetrievedDoc
    rerank_score: float


@dataclass
class CrossEncoderReranker:
    model_name: str = DEFAULT_RERANKER_MODEL

    def __post_init__(self) -> None:
        self._model = CrossEncoder(self.model_name)

    def rerank(self, query: str, docs: Sequence[RetrievedDoc], top_k: int = 3) -> List[RerankedDoc]:
        if not docs:
            return []

        pairs = [(query, d.text) for d in docs]
        scores = self._model.predict(pairs)

        reranked = [
            RerankedDoc(doc=docs[i], rerank_score=float(scores[i])) for i in range(len(docs))
        ]
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)
        return reranked[:top_k]
