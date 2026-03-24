from __future__ import annotations

from pathlib import Path
import time

from backend.schemas.contracts import AnalyzeContractResponse, ClauseLawCheck
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
    explain_max_clauses: int = 0,
    law_check_max_clauses: int = 8,
) -> AnalyzeContractResponse:
    t0 = time.perf_counter()
    clauses = extract_clauses(contract_path)
    t1 = time.perf_counter()
    graph, edges, vectors = build_document_graph(clauses, similarity_threshold=similarity_threshold)
    _ = graph
    t2 = time.perf_counter()

    contradictions = find_internal_contradictions(
        clauses=clauses,
        edges=edges,
        contradiction_threshold=contradiction_threshold,
    )
    t3 = time.perf_counter()
    risks = score_all_clauses(clauses, clause_vectors=vectors)
    t4 = time.perf_counter()

    risk_by_clause = {item.clause_index: item for item in risks}
    clause_by_index = {c.index: c for c in clauses}
    vector_by_index = {clauses[i].index: vectors[i] for i in range(len(clauses))}

    sorted_by_risk = sorted(
        [r for r in risks if r.clause_index in clause_by_index],
        key=lambda r: r.top_score,
        reverse=True,
    )
    if law_check_max_clauses > 0:
        selected_risks = sorted_by_risk[:law_check_max_clauses]
    else:
        selected_risks = []

    selected_clauses = [clause_by_index[r.clause_index] for r in selected_risks]
    selected_vectors = [vector_by_index[r.clause_index] for r in selected_risks]

    selected_law_checks = check_against_law(
        clauses=selected_clauses,
        clause_vectors=selected_vectors,
        top_k_raw=top_k_raw,
        top_k_final=top_k_final,
        contradiction_threshold=contradiction_threshold,
    ) if selected_clauses else []
    t5 = time.perf_counter()

    selected_map = {item.clause_index: item for item in selected_law_checks}
    law_checks = [
        selected_map.get(c.index, ClauseLawCheck(clause_index=c.index, law_matches=[]))
        for c in clauses
    ]

    contradictions_by_clause: dict[int, list] = {c.index: [] for c in clauses}
    for c in contradictions:
        contradictions_by_clause.setdefault(c.clause_a_index, []).append(c)
        contradictions_by_clause.setdefault(c.clause_b_index, []).append(c)

    law_by_clause = {item.clause_index: item.law_matches for item in law_checks}

    candidates = []
    for clause in clauses:
        risk = risk_by_clause.get(clause.index)
        if not risk:
            continue
        if explain_top_risks_only and risk.top_score < explain_risk_threshold:
            continue
        candidates.append((clause, risk))

    candidates.sort(key=lambda item: item[1].top_score, reverse=True)
    if explain_max_clauses == 0:
        candidates = []
    elif explain_max_clauses > 0:
        candidates = candidates[:explain_max_clauses]

    explanations = []
    for clause, risk in candidates:

        explanation = explain_clause(
            clause=clause,
            risk=risk,
            contradictions=contradictions_by_clause.get(clause.index, []),
            law_matches=law_by_clause.get(clause.index, []),
        )
        explanations.append(explanation)
    t6 = time.perf_counter()

    print(
        "[ContractLens][timing] "
        f"parse={t1 - t0:.2f}s "
        f"graph={t2 - t1:.2f}s "
        f"contradictions={t3 - t2:.2f}s "
        f"risk={t4 - t3:.2f}s "
        f"law_check={t5 - t4:.2f}s "
        f"explain={t6 - t5:.2f}s "
        f"total={t6 - t0:.2f}s "
        f"clauses={len(clauses)} selected_law={len(selected_clauses)} explanations={len(explanations)}"
    )

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
