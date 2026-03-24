from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

from backend.schemas.contracts import Clause


_CLAUSE_HEADER_RE = re.compile(
    r"(?im)^\s*(clause\s+\d+[a-zA-Z]?|\d+(?:\.\d+){0,3}[a-zA-Z]?)\s*[\)\].:-]?\s+"
)


def _compact_clause_texts(texts: list[str], min_chars: int = 140, max_clauses: int = 220) -> list[str]:
    """Merge short OCR fragments and cap total clause count to keep graph runtime bounded."""
    merged: list[str] = []
    buf = ""

    for raw in texts:
        t = raw.strip()
        if not t:
            continue
        if not buf:
            buf = t
            continue
        if len(buf) < min_chars:
            buf = f"{buf} {t}".strip()
        else:
            merged.append(buf)
            buf = t

    if buf:
        merged.append(buf)

    if len(merged) <= max_clauses or max_clauses <= 0:
        return merged

    # Merge neighboring clauses in fixed windows until we fit the cap.
    window = (len(merged) + max_clauses - 1) // max_clauses
    reduced: list[str] = []
    for i in range(0, len(merged), window):
        reduced.append("\n\n".join(merged[i : i + window]))
    return reduced


def _extract_pdf_text_with_page_breaks(pdf_path: Path) -> str:
    with fitz.open(pdf_path) as doc:
        pages = [doc.load_page(i).get_text("text") for i in range(doc.page_count)]
    return "\n\n".join(pages)


def _normalize_text(text: str) -> str:
    clean = text.replace("\r\n", "\n").replace("\r", "\n")
    clean = re.sub(r"\t+", " ", clean)
    clean = re.sub(r"[ ]{2,}", " ", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


def _fallback_paragraph_split(text: str, target_chars: int = 1400) -> list[Clause]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    clauses: list[Clause] = []
    current = ""
    index = 1

    for p in paragraphs:
        if len(current) + len(p) < target_chars:
            current = f"{current}\n\n{p}".strip()
            continue

        if current:
            clauses.append(Clause(index=index, label=f"Clause {index}", text=current))
            index += 1
        current = p

    if current:
        clauses.append(Clause(index=index, label=f"Clause {index}", text=current))

    return clauses


def extract_clauses(pdf_path: str | Path) -> list[Clause]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {path}")

    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = payload.get("clauses", []) if isinstance(payload, dict) else []
        raw_texts: list[str] = []
        for item in raw:
            if isinstance(item, dict):
                text = str(item.get("clause_text") or item.get("text") or "").strip()
            else:
                text = str(item).strip()
            if len(text) < 20:
                continue
            raw_texts.append(text)

        compacted = _compact_clause_texts(raw_texts)
        clauses = [Clause(index=i + 1, label=f"Clause {i + 1}", text=t) for i, t in enumerate(compacted)]
        return clauses

    text = _normalize_text(_extract_pdf_text_with_page_breaks(path))
    if not text:
        return []

    matches = list(_CLAUSE_HEADER_RE.finditer(text))
    if not matches:
        return _fallback_paragraph_split(text)

    clauses: list[Clause] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        header = match.group(1).strip()
        label = header.title() if header.lower().startswith("clause") else f"Clause {header}"

        if body:
            clauses.append(Clause(index=i + 1, label=label, text=body))

    if not clauses:
        return _fallback_paragraph_split(text)

    compacted = _compact_clause_texts([c.text for c in clauses])
    return [Clause(index=i + 1, label=f"Clause {i + 1}", text=t) for i, t in enumerate(compacted)]
