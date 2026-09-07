from __future__ import annotations

import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.rag.embeddings import DEFAULT_EMBEDDING_MODEL, EmbeddingModel
from backend.rag.qdrant_storage import create_payload_indexes, validate_collection


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_input_file(*candidates: str) -> Path:
    root = _repo_root()
    for candidate in candidates:
        path = root / candidate
        if path.exists():
            return path
    joined = ", ".join(str(root / c) for c in candidates)
    raise FileNotFoundError(f"Input file not found. Tried: {joined}")


def _load_backend_env() -> None:
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=backend_env, override=False)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

_ACT_FULL_NAMES: Dict[str, str] = {
    "contract_act": "Indian Contract Act, 1872",
    "ipc": "Indian Penal Code, 1860",
    "constitution": "Constitution of India",
}


def _safe_id_part(value: str) -> str:
    v = re.sub(r"\s+", "_", (value or "").strip())
    v = re.sub(r"[^A-Za-z0-9_]+", "_", v)
    v = re.sub(r"_+", "_", v).strip("_")
    return v


def _doc_id(act: str, section_number: str) -> str:
    return f"{act}_{section_number}"


def _point_uuid(doc_id: str) -> str:
    # Qdrant point ids must be UUID or unsigned int in this deployment.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"contractlens:{doc_id}"))


def _normalize_section_number(raw: Any) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    s = re.sub(r"^(section|article)\s+", "", s.strip(), flags=re.IGNORECASE)
    s = s.strip()
    return _safe_id_part(s) or s


def _drop_page_noise_lines(lines: Sequence[str]) -> List[str]:
    out: List[str] = []
    for i, line in enumerate(lines):
        l = line.strip()
        if not l:
            out.append("")
            continue

        # Typical page markers
        if re.fullmatch(r"(?i)page\s*\d+", l):
            out.append("")
            continue

        # Standalone page-number-like lines: only digits, surrounded by blanks.
        if re.fullmatch(r"\d{1,4}", l):
            prev_blank = i == 0 or not lines[i - 1].strip()
            next_blank = i == len(lines) - 1 or not lines[i + 1].strip()
            if prev_blank and next_blank:
                out.append("")
                continue

        out.append(line)
    return out


def _clean_section_text(text: str) -> str:
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = t.split("\n")
    lines = _drop_page_noise_lines(lines)

    # Normalize whitespace but preserve paragraph breaks.
    cleaned_lines: List[str] = []
    for line in lines:
        cleaned_lines.append(re.sub(r"\s+", " ", line).strip())
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


_REF_RE = re.compile(r"\b(Section|Article)\s+(\d{1,3}[A-Z]?)\b")


def _extract_references(text: str, limit: int = 25) -> List[str]:
    refs: List[str] = []
    seen: Set[str] = set()
    for m in _REF_RE.finditer(text or ""):
        ref = f"{m.group(1)} {m.group(2)}"
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
        if len(refs) >= limit:
            break
    return refs


_STOPWORDS: Set[str] = {
    "the",
    "and",
    "or",
    "of",
    "to",
    "in",
    "a",
    "an",
    "for",
    "on",
    "with",
    "by",
    "is",
    "are",
    "be",
    "shall",
    "may",
    "such",
    "any",
    "every",
    "person",
    "act",
    "section",
    "article",
    "law",
    "india",
    "indian",
}


def _extract_keywords(text: str, limit: int = 12) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
    freq: Dict[str, int] = {}
    for tok in tokens:
        if tok in _STOPWORDS:
            continue
        freq[tok] = freq.get(tok, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:limit]]


def _format_chunk_text(act_full_name: str, section_number: str, title: str, clean_section_text: str) -> str:
    return (
        f"[ACT: {act_full_name}]\n"
        f"[SECTION: {section_number}]\n"
        f"[TITLE: {title}]\n\n"
        f"{clean_section_text.strip()}\n"
    )


_CONTRACT_SECTION_START = re.compile(
    r"(?m)(?:^|\n)\s*(?:\d+\[)?(?P<num>\d{1,3}[A-Z]?)\s*\.\s*(?P<title>.{0,120}?)\s*[—–-]"
)


def _split_contract_text(text: str) -> List[Tuple[str, str, Optional[str]]]:
    """Split a Contract Act blob into (section_num, section_text, extracted_title).

    We only split on patterns that look like real section headers (must contain an em-dash/"—" style separator
    within the next ~120 chars). This avoids splitting on many footnote-like "4.Thewords..." fragments.
    """

    matches = list(_CONTRACT_SECTION_START.finditer(text))
    if not matches:
        return [("", text.strip(), None)]

    chunks: List[Tuple[str, str, Optional[str]]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sec_text = text[start:end].strip()
        sec_num = m.group("num").strip()
        title = (m.group("title") or "").strip() or None
        chunks.append((sec_num, sec_text, title))
    return chunks


def _strip_contract_heading(section_text: str, sec_num: str) -> str:
    # Remove leading "10. Title —" heading from the chunk body when present.
    t = section_text.lstrip()
    if not sec_num:
        return t
    pattern = re.compile(rf"^\s*(?:\d+\[)?{re.escape(sec_num)}\s*\.\s*.*?[—–-]\s*", re.DOTALL)
    return pattern.sub("", t, count=1).lstrip()


def iter_contract_act_docs(path: Path, version: str = "latest") -> Iterable[Dict[str, Any]]:
    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        raw_text = str(item.get("text") or "").strip()
        if not raw_text:
            continue

        # Split to ensure 1 chunk == 1 section.
        splits = _split_contract_text(raw_text)
        if len(splits) == 1 and splits[0][0] == "":
            # Fallback if we couldn't detect section headers.
            sec_num_raw = _normalize_section_number(item.get("section_number")) or str(idx)
            section_number = sec_num_raw
            title = str(item.get("title") or "").strip()
            act = "contract_act"
            act_full = _ACT_FULL_NAMES[act]
            body = _clean_section_text(raw_text)
            payload_text = _format_chunk_text(act_full, section_number, title, body)
            logical_id = _doc_id(act, section_number)
            point_id = _point_uuid(logical_id)
            yield {
                "id": point_id,
                "doc_id": logical_id,
                "act": act,
                "act_full_name": act_full,
                "section_number": section_number,
                "title": title,
                "type": "section",
                "version": version,
                "text": payload_text,
                "keywords": _extract_keywords(body),
                "references": _extract_references(body),
            }
            continue

        for sub_idx, (sec_num, sec_text, title_raw) in enumerate(splits):
            section_number = _normalize_section_number(sec_num) or _normalize_section_number(item.get("section_number")) or str(idx)
            title = (title_raw or str(item.get("title") or "")).strip()
            act = "contract_act"
            act_full = _ACT_FULL_NAMES[act]
            body = _clean_section_text(_strip_contract_heading(sec_text, sec_num))
            payload_text = _format_chunk_text(act_full, section_number, title, body)
            logical_id = _doc_id(act, section_number)
            point_id = _point_uuid(logical_id)
            yield {
                "id": point_id,
                "doc_id": logical_id,
                "act": act,
                "act_full_name": act_full,
                "section_number": section_number,
                "title": title,
                "type": "section",
                "version": version,
                "text": payload_text,
                "keywords": _extract_keywords(body),
                "references": _extract_references(body),
            }


def iter_ipc_docs(path: Path, version: str = "latest") -> Iterable[Dict[str, Any]]:
    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        raw_body = str(item.get("section_desc") or "").strip()
        if not raw_body:
            continue

        sec = item.get("Section")
        section_number = _normalize_section_number(sec) or str(idx)
        title = str(item.get("section_title") or "").strip()
        act = "ipc"
        act_full = _ACT_FULL_NAMES[act]
        body = _clean_section_text(raw_body)
        payload_text = _format_chunk_text(act_full, section_number, title, body)
        logical_id = _doc_id(act, section_number)
        point_id = _point_uuid(logical_id)

        yield {
            "id": point_id,
            "doc_id": logical_id,
            "act": act,
            "act_full_name": act_full,
            "section_number": section_number,
            "title": title,
            "type": "section",
            "version": version,
            "text": payload_text,
            "keywords": _extract_keywords(body),
            "references": _extract_references(body),
        }


def iter_constitution_docs(path: Path, version: str = "latest") -> Iterable[Dict[str, Any]]:
    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        raw_body = str(item.get("description") or "").strip()
        if not raw_body:
            continue

        article = item.get("article")
        if article == 0:
            section_number = "preamble"
        else:
            section_number = _normalize_section_number(article) or str(idx)

        title = str(item.get("title") or ("Preamble" if article == 0 else "")).strip()
        act = "constitution"
        act_full = _ACT_FULL_NAMES[act]
        body = _clean_section_text(raw_body)
        payload_text = _format_chunk_text(act_full, section_number, title, body)
        logical_id = _doc_id(act, section_number)
        point_id = _point_uuid(logical_id)

        yield {
            "id": point_id,
            "doc_id": logical_id,
            "act": act,
            "act_full_name": act_full,
            "section_number": section_number,
            "title": title,
            "type": "section",
            "version": version,
            "text": payload_text,
            "keywords": _extract_keywords(body),
            "references": _extract_references(body),
        }


def rebuild_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    if client.collection_exists(collection_name):
        print(f"Deleting existing collection '{collection_name}'...")
        client.delete_collection(collection_name)

    print(f"Creating collection '{collection_name}' (vector size={vector_size})...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    create_payload_indexes(client, collection_name=collection_name)


def upsert_docs(
    client: QdrantClient,
    collection_name: str,
    embedder: EmbeddingModel,
    docs: Iterable[Dict[str, Any]],
    batch_size: int = 16,
) -> int:
    buffer_docs: List[Dict[str, Any]] = []
    total = 0
    seen_doc_ids: Set[str] = set()

    def flush() -> int:
        nonlocal buffer_docs
        if not buffer_docs:
            return 0

        texts = [str(d["text"]) for d in buffer_docs]
        vectors = embedder.embed_texts(texts, batch_size=min(32, batch_size))
        points = [
            PointStruct(id=str(d["id"]), vector=vectors[i], payload=buffer_docs[i])
            for i, d in enumerate(buffer_docs)
        ]
        client.upsert(collection_name=collection_name, points=points, timeout=300)
        flushed = len(points)
        buffer_docs = []
        return flushed

    for doc in docs:
        doc_id = str(doc.get("doc_id") or "")
        point_id = str(doc.get("id") or "")
        if not doc_id:
            raise ValueError("Doc missing doc_id")
        if not point_id:
            raise ValueError("Doc missing point id")
        if doc_id in seen_doc_ids:
            raise ValueError(f"Duplicate deterministic doc_id generated: {doc_id}")
        seen_doc_ids.add(doc_id)

        buffer_docs.append(doc)
        if len(buffer_docs) >= batch_size:
            total += flush()
            print(f"  Upserted {total} points...")

    total += flush()
    return total, seen_doc_ids


def main() -> None:
    _load_backend_env()

    api_key = os.getenv("QDRANT_API_KEY")
    if not api_key:
        raise SystemExit("QDRANT_API_KEY not found. Add it to backend/.env")

    url = os.getenv(
        "QDRANT_URL",
        "https://5d12e4e3-03ea-4848-b40c-a1ed6490a4c5.eu-central-1-0.aws.cloud.qdrant.io",
    )
    collection_name = os.getenv("QDRANT_COLLECTION", "contractlens_legal")
    model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    version = os.getenv("LEGAL_VERSION", "latest")

    contract_path = _resolve_input_file(
        "data/default/indian_contract_act_1872_cleaned.json",
        "data/default/indian_contract_act_1872.json",
        "data/json/indian_contract_act_1872_cleaned.json",
    )
    constitution_path = _resolve_input_file(
        "data/default/constitution_of_india.json",
        "data/json/constitution_of_india.json",
    )
    ipc_path = _resolve_input_file(
        "data/default/ipc.json",
        "data/json/ipc.json",
    )

    print(f"Qdrant URL: {url}")
    print(f"Collection: {collection_name}")
    print(f"Embedding model: {model_name}")
    print(f"Version: {version}")

    client = QdrantClient(url=url, api_key=api_key)
    embedder = EmbeddingModel(model_name=model_name)

    rebuild_collection(client, collection_name=collection_name, vector_size=embedder.dimension)

    total = 0
    all_ids: Set[str] = set()
    print("\nIngesting Contract Act...")
    inserted, ids = upsert_docs(
        client,
        collection_name,
        embedder,
        iter_contract_act_docs(contract_path, version=version),
    )
    total += inserted
    all_ids |= ids

    print("\nIngesting Constitution...")
    inserted, ids = upsert_docs(
        client,
        collection_name,
        embedder,
        iter_constitution_docs(constitution_path, version=version),
    )
    total += inserted
    all_ids |= ids

    print("\nIngesting IPC...")
    inserted, ids = upsert_docs(
        client,
        collection_name,
        embedder,
        iter_ipc_docs(ipc_path, version=version),
    )
    total += inserted
    all_ids |= ids

    print(f"\nDone. Total points ingested: {total}")

    # Post-ingest validation
    count = client.count(collection_name=collection_name, exact=True).count
    if count != len(all_ids):
        raise SystemExit(
            f"Validation failed: Qdrant count={count} but expected unique ids={len(all_ids)} "
            "(duplicates may have overwritten points)."
        )

    issues = validate_collection(client, collection_name=collection_name, expected_doc_ids=all_ids)
    if issues:
        print("\nValidation issues:")
        for iss in issues[:25]:
            print(f"- {iss.point_id}: {iss.message}")
        raise SystemExit(f"Validation failed with {len(issues)} issue(s).")

    print("Validation: OK")


if __name__ == "__main__":
    main()
