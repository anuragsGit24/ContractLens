from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from backend.core.config import get_settings
from backend.services.model_singleton import embed, embed_single

if TYPE_CHECKING:
    from qdrant_client import QdrantClient


class EmbeddingAdapter:
    """Compatibility adapter for existing call sites expecting embedder methods."""

    def embed_texts(self, texts, batch_size: int = 32):
        return embed(texts, batch_size=batch_size).tolist()

    def embed_query(self, query: str):
        return embed_single(query).tolist()


@lru_cache(maxsize=2)
def get_embedder() -> EmbeddingAdapter:
    return EmbeddingAdapter()


@lru_cache(maxsize=2)
def get_qdrant_client() -> "QdrantClient":
    from qdrant_client import QdrantClient

    settings = get_settings()
    url = (settings.qdrant_url or "").strip()
    if url.lower() in ("local", "embedded", "") or not (url.startswith("http://") or url.startswith("https://")):
        db_path = settings.data_root / "qdrant_storage"
        db_path.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(db_path))

    if settings.qdrant_api_key:
        return QdrantClient(url=url, api_key=settings.qdrant_api_key, timeout=8)
    return QdrantClient(url=url, timeout=8)
