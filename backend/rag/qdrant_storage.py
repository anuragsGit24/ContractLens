from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from qdrant_client.models import Distance, VectorParams


REQUIRED_PAYLOAD_KEYS: Tuple[str, ...] = (
    "doc_id",
    "act",
    "act_full_name",
    "section_number",
    "title",
    "type",
    "version",
    "text",
)


def _expected_point_uuid(doc_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"contractlens:{doc_id}"))


@dataclass(frozen=True)
class ValidationIssue:
    point_id: str
    message: str


def recreate_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def create_payload_indexes(client: QdrantClient, collection_name: str) -> None:
    # Qdrant requires payload indexes for filtered fields.
    for field_name in ("act", "section_number", "type"):
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )
        except Exception as exc:
            # Ignore "already exists" errors to allow idempotent runs.
            msg = str(exc).lower()
            if "already" in msg and "exist" in msg:
                continue
            raise


def scroll_all_points(
    client: QdrantClient,
    collection_name: str,
    batch_size: int = 256,
) -> Iterable[qm.Record]:
    offset: Optional[qm.PointId] = None
    while True:
        records, next_offset = client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for r in records:
            yield r
        if next_offset is None:
            break
        offset = next_offset


_TEXT_HEADER_RE = re.compile(
    r"^\[ACT: .*?\]\s*\n\[SECTION: .*?\]\s*\n\[TITLE: .*?\]\s*\n\s*\n",
    re.DOTALL,
)


def validate_collection(
    client: QdrantClient,
    collection_name: str,
    expected_doc_ids: Optional[Set[str]] = None,
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    seen_doc_ids: Set[str] = set()

    for rec in scroll_all_points(client, collection_name=collection_name):
        point_id = str(rec.id)

        payload = dict(rec.payload or {})
        if not payload:
            issues.append(ValidationIssue(point_id=point_id, message="Missing payload"))
            continue

        missing = [k for k in REQUIRED_PAYLOAD_KEYS if k not in payload]
        if missing:
            issues.append(ValidationIssue(point_id=point_id, message=f"Missing payload keys: {missing}"))
            continue

        # Deterministic id checks
        act = str(payload.get("act") or "")
        section_number = str(payload.get("section_number") or "")
        expected_doc_id = f"{act}_{section_number}"
        doc_id = str(payload.get("doc_id") or "")
        if doc_id != expected_doc_id:
            issues.append(
                ValidationIssue(
                    point_id=point_id,
                    message=f"doc_id mismatch (expected {expected_doc_id} from payload act/section_number)",
                )
            )

        expected_uuid = _expected_point_uuid(doc_id)
        if point_id != expected_uuid:
            issues.append(
                ValidationIssue(
                    point_id=point_id,
                    message="Point id is not deterministic UUIDv5(contractlens:doc_id)",
                )
            )

        if doc_id in seen_doc_ids:
            issues.append(ValidationIssue(point_id=point_id, message=f"Duplicate doc_id in payload: {doc_id}"))
        else:
            seen_doc_ids.add(doc_id)

        # Text formatting check
        text = str(payload.get("text") or "")
        if not _TEXT_HEADER_RE.search(text):
            issues.append(
                ValidationIssue(
                    point_id=point_id,
                    message="Text is not in expected header format ([ACT]/[SECTION]/[TITLE] + blank line)",
                )
            )

    if expected_doc_ids is not None:
        missing_ids = sorted(expected_doc_ids - seen_doc_ids)
        extra_ids = sorted(seen_doc_ids - expected_doc_ids)
        if missing_ids:
            issues.append(
                ValidationIssue(
                    point_id="<collection>",
                    message=f"Missing doc_ids in Qdrant: {missing_ids[:10]}",
                )
            )
        if extra_ids:
            issues.append(
                ValidationIssue(
                    point_id="<collection>",
                    message=f"Unexpected doc_ids in Qdrant: {extra_ids[:10]}",
                )
            )

    return issues
