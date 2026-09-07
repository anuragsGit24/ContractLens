from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.rag.embeddings import DEFAULT_EMBEDDING_MODEL, EmbeddingModel
from backend.rag.pipeline import retrieve_top_sections


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_backend_env() -> None:
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=backend_env, override=False)


def _resolve_ipc_path(root: Path) -> Path:
    candidates = [
        root / "data" / "json" / "ipc.json",
        root / "data" / "default" / "ipc.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    tried = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(f"IPC json not found. Tried: {tried}")


def main() -> None:
    # Keep output readable: enable DEBUG only for our RAG logger, not for all third-party libs.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("contractlens.rag").setLevel(logging.DEBUG)
    for noisy in (
        "httpx",
        "httpcore",
        "filelock",
        "urllib3",
        "huggingface_hub",
        "sentence_transformers",
        "transformers",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)
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

    client = QdrantClient(url=url, api_key=api_key)
    embedder = EmbeddingModel(model_name=model_name)

    # 1) Collection stats
    count = client.count(collection_name=collection_name, exact=True)
    print(f"Collection '{collection_name}' count: {count.count}")

    # 2) End-to-end pipeline test (includes metadata filtering + reranking + debug logs)
    queries = [
        "If any provision of this Agreement is held invalid, the remainder shall continue in full force and effect. Consequently, this applies to Section 1.",
        "The Promoter may terminate this Agreement for Sale without notice and forfeit the entire amount if the Allottee is delayed in payment by a single day.",
        "What is equality before law?",
    ]

    for q in queries:
        result = retrieve_top_sections(q)
        print("\n=== QUERY ===")
        print(q)
        print("Act filter:", result.act_filter)
        print("Top-3 (post rerank):")
        for i, d in enumerate(result.top3, start=1):
            title = d.payload.get("title")
            print(f"{i}. {d.act} | {d.section_number} | {title}")

    # 3) Vector-space self-retrieval sanity check using IPC Section 1
    root = _repo_root()
    ipc_path = _resolve_ipc_path(root)
    ipc_data = json.loads(ipc_path.read_text(encoding="utf-8"))
    ipc_1 = next((x for x in ipc_data if isinstance(x, dict) and x.get("Section") == 1), None)
    if not ipc_1:
        raise SystemExit("Could not find IPC Section 1 in ipc.json")

    expected_section = "1"
    expected_act = "ipc"
    text = str(ipc_1.get("section_desc") or "").strip()
    if not text:
        raise SystemExit("IPC Section 1 text is empty")

    v = embedder.embed_query(text)
    hit = client.query_points(
        collection_name=collection_name,
        query=v,
        limit=1,
        with_payload=True,
    ).points

    if not hit:
        raise SystemExit("Self-retrieval failed: no results returned")

    payload = hit[0].payload or {}
    got_act = payload.get("act")
    got_section = payload.get("section_number")
    ok = got_act == expected_act and got_section == expected_section

    print("\nSelf-retrieval (IPC Section 1):")
    print("Expected:", expected_act, expected_section)
    print("Got:     ", got_act, got_section)
    print("PASS" if ok else "FAIL")

    if not ok:
        raise SystemExit("Self-retrieval check failed. Re-ingest the collection with the new schema/model.")


if __name__ == "__main__":
    main()
