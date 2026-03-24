from __future__ import annotations

from itertools import combinations

import networkx as nx
import numpy as np

from backend.schemas.contracts import Clause, GraphEdge, InternalContradiction
from backend.services.contradiction_detector import detect_contradiction
from backend.services.model_singleton import embed


def build_document_graph(
    clauses: list[Clause],
    similarity_threshold: float = 0.75,
) -> tuple[nx.Graph, list[GraphEdge], list[list[float]]]:
    if not clauses:
        return nx.Graph(), [], []

    clause_texts = [c.text[:1200] for c in clauses]
    vectors = embed(clause_texts).tolist()

    graph = nx.Graph()
    for clause in clauses:
        graph.add_node(clause.index, label=clause.label, text=clause.text)

    # Vectors are normalized, so matrix multiplication yields cosine similarity.
    mat = np.asarray(vectors, dtype=np.float32)
    sim_matrix = mat @ mat.T

    edges: list[GraphEdge] = []
    for i, j in combinations(range(len(clauses)), 2):
        similarity = float(sim_matrix[i, j])
        if similarity >= similarity_threshold:
            source = clauses[i].index
            target = clauses[j].index
            graph.add_edge(source, target, similarity=similarity)
            edges.append(
                GraphEdge(
                    source_index=source,
                    target_index=target,
                    similarity=similarity,
                )
            )

    return graph, edges, vectors


def find_internal_contradictions(
    clauses: list[Clause],
    edges: list[GraphEdge],
    contradiction_threshold: float = 0.68,
    max_pairs: int = 25,
) -> list[InternalContradiction]:
    if not clauses or not edges:
        return []

    by_index = {c.index: c for c in clauses}

    conflict_zone_edges = [e for e in edges if 0.72 < float(e.similarity) < 0.89]
    if conflict_zone_edges:
        candidate_edges = sorted(conflict_zone_edges, key=lambda e: e.similarity, reverse=True)
    else:
        # If all similarities are very high, pick edges closest to the conflict center.
        target = 0.90
        candidate_edges = sorted(edges, key=lambda e: abs(float(e.similarity) - target))
    if max_pairs > 0:
        candidate_edges = candidate_edges[:max_pairs]

    contradictions: list[InternalContradiction] = []
    for edge in candidate_edges:
        clause_a = by_index.get(edge.source_index)
        clause_b = by_index.get(edge.target_index)
        if not clause_a or not clause_b:
            continue

        decision = detect_contradiction(
            text_a=clause_a.text,
            text_b=clause_b.text,
            sim_score=float(edge.similarity),
        )
        score = float(decision.get("confidence", 0.0))
        # Keep threshold semantics in response flow.
        model_like_score = score if score <= 1.0 else np.clip(score, 0.0, 1.0)
        is_contradiction = bool(decision.get("is_contradiction", False))
        is_tension = "possible tension" in str(decision.get("reason", "")).lower()
        tension_threshold = max(0.30, contradiction_threshold * 0.55)
        if is_contradiction and (
            model_like_score >= contradiction_threshold
            or (is_tension and model_like_score >= tension_threshold)
        ):
            contradictions.append(
                InternalContradiction(
                    clause_a_index=clause_a.index,
                    clause_b_index=clause_b.index,
                    contradiction_score=model_like_score,
                )
            )

    contradictions.sort(key=lambda x: x.contradiction_score, reverse=True)
    return contradictions
