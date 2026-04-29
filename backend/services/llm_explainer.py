from __future__ import annotations

import re
from typing import Iterable

import requests

from backend.core.config import get_settings
from backend.schemas.contracts import (
    CitationVerification,
    Clause,
    ClauseExplanation,
    ClauseRisk,
    InternalContradiction,
    LawMatch,
)

_CITATION_RE = re.compile(r"\b(?:Section|Article)\s+([0-9]{1,3}[A-Za-z]?)\b", re.IGNORECASE)


def _ollama_available(base_url: str) -> bool:
    """Use a quick probe before generation and retry each call to avoid stale status."""
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=2)
        return bool(resp.ok)
    except Exception:
        return False


def build_prompt(
    clause: Clause,
    risk: ClauseRisk,
    contradictions: list[InternalContradiction],
    law_matches: list[LawMatch],
) -> str:
    contradiction_lines = [
        f"- Clause {c.clause_a_index} vs Clause {c.clause_b_index} | score={c.contradiction_score:.3f}"
        for c in contradictions
    ]

    law_lines = [
        f"- {m.act} Section {m.section_number}: {m.title} | contradiction_score={m.contradiction_score:.3f}"
        for m in law_matches
    ]

    return (
        "You are a legal contract analyst for Indian business agreements.\n"
        "Provide a concise plain-English risk explanation for the clause below.\n"
        "Cite only statutes present in the retrieved list.\n"
        "If evidence is weak, clearly say uncertainty.\n\n"
        f"Clause Label: {clause.label}\n"
        f"Clause Text:\n{clause.text}\n\n"
        f"Top Risk Category: {risk.top_category}\n"
        f"Risk Score: {risk.top_score:.3f}\n"
        f"Risk Level: {risk.risk_level}\n\n"
        + (
            f"Relative Risk Level (dataset-calibrated): {risk.risk_level_relative}\n\n"
            if risk.risk_level_relative
            else ""
        )
        + "Internal Contradictions:\n"
        + ("\n".join(contradiction_lines) if contradiction_lines else "- None")
        + "\n\nRetrieved Law Matches:\n"
        + ("\n".join(law_lines) if law_lines else "- None")
        + "\n\n"
        "Output format:\n"
        "1) Risk Summary\n"
        "2) Why risky under Indian law\n"
        "3) Practical impact on business\n"
        "4) Safer rewrite suggestion\n"
        "5) Citations (Section/Article references only from provided list)\n"
    )


def _extract_citations(text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for match in _CITATION_RE.findall(text or ""):
        normalized = match.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def _expected_citations(law_matches: Iterable[LawMatch]) -> set[str]:
    return {str(m.section_number).strip().lower() for m in law_matches if str(m.section_number).strip()}


def verify_citations(generated_text: str, law_matches: list[LawMatch]) -> CitationVerification:
    extracted = _extract_citations(generated_text)
    supported_set = _expected_citations(law_matches)
    supported = [c for c in extracted if c in supported_set]
    unsupported = [c for c in extracted if c not in supported_set]
    return CitationVerification(
        extracted_citations=extracted,
        supported_citations=supported,
        unsupported_citations=unsupported,
        passed=len(unsupported) == 0,
    )


def explain_clause(
    clause: Clause,
    risk: ClauseRisk,
    contradictions: list[InternalContradiction],
    law_matches: list[LawMatch],
) -> ClauseExplanation:
    settings = get_settings()
    base_url = settings.ollama_url.rstrip("/")
    prompt = build_prompt(clause=clause, risk=risk, contradictions=contradictions, law_matches=law_matches)

    warning = None
    explanation = ""
    if not _ollama_available(base_url):
        warning = f"Ollama unavailable at {base_url}; skipped remote generation for fast response."
        explanation = (
            "LLM explanation is temporarily unavailable. "
            "Use risk score and retrieved law matches for manual review."
        )
        verification = verify_citations(explanation, law_matches)
        return ClauseExplanation(
            clause_index=clause.index,
            explanation=explanation,
            prompt=prompt,
            citation_verification=verification,
            model_name=settings.ollama_model,
            warning=warning,
        )

    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
        explanation = str(payload.get("response") or "").strip()
        if not explanation:
            warning = "Ollama returned an empty response payload."
            explanation = (
                "LLM explanation returned no text. "
                "Use risk score and retrieved law matches for manual review."
            )
    except Exception as exc:
        warning = f"Ollama call failed: {exc}"
        explanation = (
            "LLM explanation is temporarily unavailable. "
            "Use risk score and retrieved law matches for manual review."
        )

    verification = verify_citations(explanation, law_matches)
    return ClauseExplanation(
        clause_index=clause.index,
        explanation=explanation,
        prompt=prompt,
        citation_verification=verification,
        model_name=settings.ollama_model,
        warning=warning,
    )
