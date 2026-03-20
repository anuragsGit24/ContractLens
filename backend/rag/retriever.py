from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm


@dataclass
class RetrievedDoc:
    id: str
    score: float
    payload: Dict[str, Any]

    @property
    def text(self) -> str:
        return str(self.payload.get("text") or "")

    @property
    def act(self) -> str:
        return str(self.payload.get("act") or "")

    @property
    def section_number(self) -> str:
        return str(self.payload.get("section_number") or self.payload.get("section") or "")


@dataclass
class QdrantRetriever:
    client: QdrantClient
    collection_name: str
    _act_index_ensured: bool = False

    def _ensure_act_index(self) -> None:
        """Ensure payload index exists for `act` to support keyword filtering.

        Qdrant requires a payload index for filtered fields (keyword type).
        """

        if self._act_index_ensured:
            return

        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="act",
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )
        except Exception as exc:  # pragma: no cover
            # If it already exists (or is being built), don't fail queries.
            msg = str(exc).lower()
            if "already exists" not in msg and "already" not in msg and "exists" not in msg:
                raise

        self._act_index_ensured = True

    def _act_filter(self, act: Optional[str]) -> Optional[qm.Filter]:
        if not act:
            return None
        return qm.Filter(
            must=[
                qm.FieldCondition(
                    key="act",
                    match=qm.MatchValue(value=act),
                )
            ]
        )

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        act: Optional[str] = None,
    ) -> List[RetrievedDoc]:
        if act:
            self._ensure_act_index()

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=self._act_filter(act),
            with_payload=True,
        )

        docs: List[RetrievedDoc] = []
        for p in response.points:
            docs.append(
                RetrievedDoc(
                    id=str(p.id),
                    score=float(p.score or 0.0),
                    payload=dict(p.payload or {}),
                )
            )
        return docs
