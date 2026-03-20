from __future__ import annotations

import re
from pathlib import Path

import fitz

from backend.schemas.contracts import Clause


_CLAUSE_HEADER_RE = re.compile(
    r"(?im)^\s*(clause\s+\d+[a-zA-Z]?|\d+(?:\.\d+){0,3}[a-zA-Z]?)\s*[\)\].:-]?\s+"
)


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

    return clauses
