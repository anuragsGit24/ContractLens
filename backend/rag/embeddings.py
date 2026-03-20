from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Sequence

from sentence_transformers import SentenceTransformer


DEFAULT_EMBEDDING_MODEL = "law-ai/InLegalBERT"


@lru_cache(maxsize=8)
def _load_sentence_transformer(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


@dataclass
class EmbeddingModel:
    model_name: str = DEFAULT_EMBEDDING_MODEL

    def __post_init__(self) -> None:
        self._model = _load_sentence_transformer(self.model_name)

    @property
    def dimension(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    def embed_texts(self, texts: Sequence[str], batch_size: int = 32) -> List[List[float]]:
        vectors = self._model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return [v.tolist() for v in vectors]

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query], batch_size=1)[0]
