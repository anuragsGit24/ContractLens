from __future__ import annotations

from backend.core.config import get_settings
from backend.core.model_registry import get_embedder, get_nli_pipeline, get_qdrant_client, get_reranker
from backend.rag.retriever import QdrantRetriever
from backend.schemas.contracts import Clause, ClauseLawCheck, LawMatch


def _contradiction_score(nli_output: list[dict]) -> float:
    for item in nli_output:
        label = str(item.get("label", "")).lower()
        if "contradict" in label:
            return float(item.get("score", 0.0))
    return 0.0


def check_against_law(
    clauses: list[Clause],
    clause_vectors: list[list[float]] | None = None,
    top_k_raw: int = 10,
    top_k_final: int = 3,
    contradiction_threshold: float = 0.68,
) -> list[ClauseLawCheck]:
    if not clauses:
        return []

    settings = get_settings()
    qdrant = get_qdrant_client()
    embedder = get_embedder()
    retriever = QdrantRetriever(client=qdrant, collection_name=settings.qdrant_collection)
    reranker = get_reranker()
    nli = get_nli_pipeline()

    vectors = clause_vectors if clause_vectors else embedder.embed_texts([c.text for c in clauses])

    output: list[ClauseLawCheck] = []
    for idx, clause in enumerate(clauses):
        vector = vectors[idx]
        raw_hits = retriever.search(query_vector=vector, limit=top_k_raw, act=None)
        reranked = reranker.rerank(query=clause.text, docs=raw_hits, top_k=top_k_final)

        matches: list[LawMatch] = []
        for hit in reranked:
            doc = hit.doc
            law_text = str(doc.payload.get("text") or "")
            nli_out = nli({"text": clause.text, "text_pair": law_text})
            if nli_out and isinstance(nli_out[0], list):
                nli_out = nli_out[0]
            contradiction_score = _contradiction_score(nli_out)

            if contradiction_score >= contradiction_threshold:
                matches.append(
                    LawMatch(
                        act=doc.act,
                        section_number=doc.section_number,
                        title=str(doc.payload.get("title") or ""),
                        text=law_text,
                        retrieval_score=float(doc.score),
                        rerank_score=float(hit.rerank_score),
                        contradiction_score=float(contradiction_score),
                    )
                )

        output.append(ClauseLawCheck(clause_index=clause.index, law_matches=matches))

    return output
