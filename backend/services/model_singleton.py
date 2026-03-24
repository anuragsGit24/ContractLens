from __future__ import annotations

from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

print("[ContractLens] Loading InLegalBERT once at startup...")
embedder = SentenceTransformer("law-ai/InLegalBERT")
print("[ContractLens] InLegalBERT ready. No other models will load.")


def embed(texts: Sequence[str], batch_size: int = 32) -> np.ndarray:
    """Embed a sequence of texts and return normalized vectors."""
    return embedder.encode(
        list(texts),
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=False,
    )


def embed_single(text: str) -> np.ndarray:
    """Embed one text and return a normalized vector."""
    return embedder.encode(text, normalize_embeddings=True)
