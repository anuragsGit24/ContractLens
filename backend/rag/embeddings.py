from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from backend.services.model_singleton import embed, embedder


DEFAULT_EMBEDDING_MODEL = "law-ai/InLegalBERT"


@dataclass
class EmbeddingModel:
    model_name: str = DEFAULT_EMBEDDING_MODEL

    @property
    def dimension(self) -> int:
        return int(embedder.get_sentence_embedding_dimension())

    def embed_texts(self, texts: Sequence[str], batch_size: int = 32) -> List[List[float]]:
        vectors = embed(list(texts), batch_size=batch_size)
        return [v.tolist() for v in vectors]

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query], batch_size=1)[0]
