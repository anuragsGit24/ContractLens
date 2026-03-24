from __future__ import annotations

import numpy as np

from backend.schemas.contracts import Clause, ClauseRisk
from backend.services.model_singleton import embed


RISK_CATEGORIES = {
    "unfair liability limitation": "party excludes or caps liability for damages breaches losses",
    "missing arbitration clause": "no arbitration or dispute resolution mechanism in contract",
    "unilateral contract termination": "one party terminates contract without cause notice or consent",
    "intellectual property overreach": "broad assignment of intellectual property rights to one party",
    "penalty clause exceeding actual loss": "penalty or damages clause exceeding reasonable compensation",
    "misrepresentation or fraud risk": "false statements misrepresentation concealment of material facts",
    "restraint of trade": "non-compete non-solicitation restriction after contract ends",
    "no dispute resolution mechanism": "no process for resolving disagreements or legal disputes",
}

_LABELS = list(RISK_CATEGORIES.keys())

print("[ContractLens] Pre-computing risk category embeddings...")
_RISK_VECS = embed(list(RISK_CATEGORIES.values()))
print("[ContractLens] Risk vectors ready.")


def _risk_level(score: float) -> str:
    """Assign absolute risk level from score only."""
    if score >= 0.72:
        return "high"
    if score >= 0.58:
        return "medium"
    return "low"


def score_risk(clause_embedding: np.ndarray) -> dict[str, str | float]:
    """Score one normalized clause embedding against pre-computed risk vectors."""
    scores = np.dot(_RISK_VECS, clause_embedding)
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])
    sorted_scores = np.sort(scores)
    second_score = float(sorted_scores[-2]) if len(sorted_scores) > 1 else best_score
    margin = best_score - second_score
    absolute_level = _risk_level(best_score)

    return {
        "risk_level": absolute_level,
        "risk_level_absolute": absolute_level,
        "risk_level_relative": absolute_level,
        "risk_type": _LABELS[best_idx],
        "confidence": round(best_score, 3),
        "margin": round(margin, 3),
    }


def score_all_clauses(clauses: list[Clause], clause_vectors: np.ndarray | None = None) -> list[ClauseRisk]:
    if not clauses:
        return []

    if clause_vectors is None:
        clause_vectors = embed([c.text[:1200] for c in clauses])
    interim: list[dict[str, float | int | str]] = []

    for idx, clause in enumerate(clauses):
        scores = np.dot(_RISK_VECS, clause_vectors[idx])
        score_map = {
            _LABELS[i]: float(scores[i])
            for i in range(len(_LABELS))
        }
        best_idx = int(np.argmax(scores))
        top_category = _LABELS[best_idx]
        top_score = float(scores[best_idx])
        sorted_scores = np.sort(scores)
        second_score = float(sorted_scores[-2]) if len(sorted_scores) > 1 else top_score
        margin = top_score - second_score
        absolute_level = _risk_level(top_score)

        interim.append(
            {
                "clause_index": clause.index,
                "top_category": top_category,
                "top_score": float(round(top_score, 3)),
                "margin": float(margin),
                "absolute_level": absolute_level,
                "score_map": score_map,
            }
        )

    # Relative calibration remains secondary metadata for ranking context.
    high_indices: set[int] = set()
    if len(interim) >= 20:
        non_low = [
            (i, item)
            for i, item in enumerate(interim)
            if str(item["absolute_level"]) != "low"
        ]
        if non_low:
            target_high = max(1, int(round(len(interim) * 0.08)))
            target_high = min(target_high, len(non_low))
            ranked = sorted(
                non_low,
                key=lambda t: (float(t[1]["top_score"]), float(t[1]["margin"])),
                reverse=True,
            )
            high_indices = {idx for idx, _ in ranked[:target_high]}

    risks: list[ClauseRisk] = []
    for i, item in enumerate(interim):
        absolute_level = str(item["absolute_level"])
        if i in high_indices:
            relative_level = "high"
        elif absolute_level == "low":
            relative_level = "low"
        else:
            relative_level = "medium"

        risks.append(
            ClauseRisk(
                clause_index=int(item["clause_index"]),
                top_category=str(item["top_category"]),
                top_score=float(item["top_score"]),
                category_scores=dict(item["score_map"]),
                risk_level=absolute_level,
                risk_level_absolute=absolute_level,
                risk_level_relative=relative_level,
            )
        )

    return risks
