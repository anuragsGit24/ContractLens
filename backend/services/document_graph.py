from __future__ import annotations

from itertools import combinations

import networkx as nx

from backend.core.model_registry import get_embedder, get_nli_pipeline
from backend.schemas.contracts import Clause, GraphEdge, InternalContradiction


def _contradiction_score(nli_output: list[dict]) -> float:
    for item in nli_output:
        label = str(item.get("label", "")).lower()
        if "contradict" in label:
            return float(item.get("score", 0.0))
    return 0.0


def build_document_graph(
    clauses: list[Clause],
    similarity_threshold: float = 0.75,
) -> tuple[nx.Graph, list[GraphEdge], list[list[float]]]:
    if not clauses:
        return nx.Graph(), [], []

    embedder = get_embedder()
    clause_texts = [c.text for c in clauses]
    vectors = embedder.embed_texts(clause_texts)

    graph = nx.Graph()
    for clause in clauses:
        graph.add_node(clause.index, label=clause.label, text=clause.text)

    edges: list[GraphEdge] = []
    for i, j in combinations(range(len(clauses)), 2):
        # Vectors are L2-normalized in embedder, so dot product is cosine similarity.
        similarity = sum(a * b for a, b in zip(vectors[i], vectors[j]))
        if similarity >= similarity_threshold:
            source = clauses[i].index
            target = clauses[j].index
            graph.add_edge(source, target, similarity=float(similarity))
            edges.append(
                GraphEdge(
                    source_index=source,
                    target_index=target,
                    similarity=float(similarity),
                )
            )

    return graph, edges, vectors


def find_internal_contradictions(
    clauses: list[Clause],
    edges: list[GraphEdge],
    contradiction_threshold: float = 0.68,
) -> list[InternalContradiction]:
    if not clauses or not edges:
        return []

    nli = get_nli_pipeline()
    by_index = {c.index: c for c in clauses}

    contradictions: list[InternalContradiction] = []
    for edge in edges:
        clause_a = by_index.get(edge.source_index)
        clause_b = by_index.get(edge.target_index)
        if not clause_a or not clause_b:
            continue

        output = nli({"text": clause_a.text, "text_pair": clause_b.text})
        if output and isinstance(output[0], list):
            output = output[0]
        score = _contradiction_score(output)
        if score >= contradiction_threshold:
            contradictions.append(
                InternalContradiction(
                    clause_a_index=clause_a.index,
                    clause_b_index=clause_b.index,
                    contradiction_score=score,
                )
            )

    contradictions.sort(key=lambda x: x.contradiction_score, reverse=True)
    return contradictions
