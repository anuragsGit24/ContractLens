from __future__ import annotations

from backend.core.constants import RISK_CATEGORIES
from backend.core.model_registry import get_zero_shot_pipeline
from backend.schemas.contracts import Clause, ClauseRisk


def _risk_level(score: float) -> str:
    if score >= 0.65:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def score_all_clauses(clauses: list[Clause]) -> list[ClauseRisk]:
    if not clauses:
        return []

    zero_shot = get_zero_shot_pipeline()
    risks: list[ClauseRisk] = []

    for clause in clauses:
        output = zero_shot(
            clause.text,
            candidate_labels=RISK_CATEGORIES,
            multi_label=True,
        )

        labels = output.get("labels", [])
        scores = output.get("scores", [])
        score_map = {str(labels[i]): float(scores[i]) for i in range(min(len(labels), len(scores)))}

        top_category = max(score_map, key=score_map.get) if score_map else "unknown"
        top_score = float(score_map.get(top_category, 0.0))
        risks.append(
            ClauseRisk(
                clause_index=clause.index,
                top_category=top_category,
                top_score=top_score,
                category_scores=score_map,
                risk_level=_risk_level(top_score),
            )
        )

    return risks
