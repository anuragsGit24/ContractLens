from __future__ import annotations

import numpy as np

from .model_singleton import embed, embed_single


def rerank(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    """Rerank chunks by cosine similarity using InLegalBERT embeddings."""
    if not chunks:
        return []

    query_vec = embed_single(query)
    chunk_texts = [str(c.get("text", ""))[:512] for c in chunks]
    chunk_vecs = embed(chunk_texts)
    scores = np.dot(chunk_vecs, query_vec)

    ranked: list[dict] = []
    for idx, chunk in enumerate(chunks):
        enriched = dict(chunk)
        enriched["rerank_score"] = float(scores[idx])
        ranked.append(enriched)

    ranked.sort(key=lambda x: float(x["rerank_score"]), reverse=True)
    return ranked[:top_k]
