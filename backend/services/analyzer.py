from __future__ import annotations

from pathlib import Path

from backend.schemas.contracts import AnalyzeContractResponse
from backend.services.document_graph import build_document_graph, find_internal_contradictions
from backend.services.document_parser import extract_clauses
from backend.services.law_checker import check_against_law
from backend.services.llm_explainer import explain_clause
from backend.services.risk_scorer import score_all_clauses


def analyze_contract(
    contract_path: str | Path,
    similarity_threshold: float = 0.75,
    contradiction_threshold: float = 0.68,
    top_k_raw: int = 10,
    top_k_final: int = 3,
    explain_top_risks_only: bool = True,
    explain_risk_threshold: float = 0.6,
) -> AnalyzeContractResponse:
    clauses = extract_clauses(contract_path)
    graph, edges, vectors = build_document_graph(clauses, similarity_threshold=similarity_threshold)
    _ = graph

    contradictions = find_internal_contradictions(
        clauses=clauses,
        edges=edges,
        contradiction_threshold=contradiction_threshold,
    )
    risks = score_all_clauses(clauses)
    law_checks = check_against_law(
        clauses=clauses,
        clause_vectors=vectors,
        top_k_raw=top_k_raw,
        top_k_final=top_k_final,
        contradiction_threshold=contradiction_threshold,
    )

    contradictions_by_clause: dict[int, list] = {c.index: [] for c in clauses}
    for c in contradictions:
        contradictions_by_clause.setdefault(c.clause_a_index, []).append(c)
        contradictions_by_clause.setdefault(c.clause_b_index, []).append(c)

    law_by_clause = {item.clause_index: item.law_matches for item in law_checks}
    risk_by_clause = {item.clause_index: item for item in risks}

    explanations = []
    for clause in clauses:
        risk = risk_by_clause.get(clause.index)
        if not risk:
            continue

        if explain_top_risks_only and risk.top_score < explain_risk_threshold:
            continue

        explanation = explain_clause(
            clause=clause,
            risk=risk,
            contradictions=contradictions_by_clause.get(clause.index, []),
            law_matches=law_by_clause.get(clause.index, []),
        )
        explanations.append(explanation)

    return AnalyzeContractResponse(
        contract_path=str(contract_path),
        clauses=clauses,
        graph_edges=edges,
        internal_contradictions=contradictions,
        risks=risks,
        law_checks=law_checks,
        explanations=explanations,
        placeholder_flags={
            "law_graph_built_once": False,
            "supabase_persistence": False,
        },
    )
