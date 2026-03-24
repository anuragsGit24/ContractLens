from __future__ import annotations

import re

POSITIVE = re.compile(
    r"\b(shall|must|guarantees|ensures|warrants|will provide|"
    r"agrees to|is obligated|is required)\b",
    re.IGNORECASE,
)

NEGATIVE = re.compile(
    r"\b(shall not|must not|not liable|no liability|not responsible|"
    r"excluded|waived|disclaims|does not|will not|is not responsible)\b",
    re.IGNORECASE,
)

SUBJECT_KEYWORDS = re.compile(
    r"\b(seller|buyer|party|liability|responsible|obligation|"
    r"quality|delivery|payment|termination|ip|intellectual property)\b",
    re.IGNORECASE,
)


def detect_contradiction(text_a: str, text_b: str, sim_score: float) -> dict[str, float | bool | str]:
    """Detect contradiction using cosine zone and obligation polarity mismatch."""
    # OCR-compacted legal clauses often cluster at high cosine scores; keep a broad zone for polarity flips.
    in_conflict_zone = 0.72 < sim_score < 0.995
    # Subtle tensions are most reliable in the medium-high similarity band.
    in_tension_zone = 0.72 < sim_score < 0.89

    a_pos = bool(POSITIVE.search(text_a))
    a_neg = bool(NEGATIVE.search(text_a))
    b_pos = bool(POSITIVE.search(text_b))
    b_neg = bool(NEGATIVE.search(text_b))
    polarity_mismatch = (a_pos and b_neg) or (a_neg and b_pos)
    shared_subject = bool(SUBJECT_KEYWORDS.search(text_a)) and bool(SUBJECT_KEYWORDS.search(text_b))

    if in_conflict_zone and polarity_mismatch:
        return {
            "is_contradiction": True,
            "confidence": round(sim_score * 0.90, 3),
            "reason": "same topic, opposing obligations",
        }
    if in_tension_zone and shared_subject:
        return {
            "is_contradiction": True,
            "confidence": round(sim_score * 0.50, 3),
            "reason": "same legal subject, possible tension",
        }

    return {"is_contradiction": False, "confidence": 0.0, "reason": ""}
