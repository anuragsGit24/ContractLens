from __future__ import annotations

import numpy as np

from backend.core.config import get_settings
from backend.core.model_registry import get_qdrant_client
from backend.rag.retriever import QdrantRetriever
from backend.schemas.contracts import Clause, ClauseLawCheck, LawMatch
from backend.services.contradiction_detector import detect_contradiction


def check_against_law(
    clauses: list[Clause],
    clause_vectors: list[list[float]] | None = None,
    top_k_raw: int = 10,
    top_k_final: int = 3,
    contradiction_threshold: float = 0.50,
) -> list[ClauseLawCheck]:
    if not clauses:
        return []

    settings = get_settings()
    qdrant = get_qdrant_client()
    retriever = QdrantRetriever(client=qdrant, collection_name=settings.qdrant_collection)

    if clause_vectors is None:
        from backend.services.model_singleton import embed

        vectors = embed([c.text[:1200] for c in clauses]).tolist()
    else:
        vectors = clause_vectors

    raw_hits_by_clause: list[list] = []
    text_pool: list[str] = []
    for idx, _ in enumerate(clauses):
        vector = vectors[idx]
        try:
            raw_hits = retriever.search(query_vector=vector, limit=top_k_raw, act=None)
        except Exception:
            raw_hits = []
        raw_hits_by_clause.append(raw_hits)
        for doc in raw_hits:
            text_pool.append(str(doc.text or "")[:512])

    unique_texts = list(dict.fromkeys(text_pool))
    text_to_vec: dict[str, np.ndarray] = {}
    if unique_texts:
        from backend.services.model_singleton import embed

        vecs = embed(unique_texts)
        for i, text in enumerate(unique_texts):
            text_to_vec[text] = vecs[i]

    output: list[ClauseLawCheck] = []
    for idx, clause in enumerate(clauses):
        clause_vec = np.asarray(vectors[idx], dtype=np.float32)
        raw_hits = raw_hits_by_clause[idx]

        scored_hits: list[tuple[float, object]] = []
        for doc in raw_hits:
            text = str(doc.text or "")[:512]
            vec = text_to_vec.get(text)
            if vec is None:
                score = float(doc.score)
            else:
                score = float(np.dot(vec, clause_vec))
            scored_hits.append((score, doc))

        scored_hits.sort(key=lambda item: item[0], reverse=True)
        top_hits = scored_hits[:top_k_final]

        matches: list[LawMatch] = []
        for sim_score, doc in top_hits:
            law_text = str(
                doc.payload.get("description")
                or doc.payload.get("text")
                or doc.payload.get("content")
                or doc.payload.get("body")
                or ""
            )
            act_number = str(
                doc.payload.get("act_number")
                or doc.payload.get("section_number")
                or doc.payload.get("section")
                or doc.section_number
                or ""
            )
            title = str(doc.payload.get("title") or "")
            contradiction = detect_contradiction(
                text_a=clause.text,
                text_b=law_text,
                sim_score=sim_score,
            )
            contradiction_score = float(contradiction.get("confidence", 0.0))

            if bool(contradiction.get("is_contradiction", False)) and contradiction_score >= contradiction_threshold:
                matches.append(
                    LawMatch(
                        act=doc.act,
                        act_number=act_number,
                        section_number=doc.section_number,
                        title=title,
                        description=law_text,
                        text=law_text,
                        retrieval_score=float(doc.score),
                        rerank_score=float(sim_score),
                        contradiction_score=float(contradiction_score),
                    )
                )

        output.append(ClauseLawCheck(clause_index=clause.index, law_matches=matches))

    return output
