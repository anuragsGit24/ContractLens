"""
Benchmark Retrieval Script for ContractLens (Task 3).
Evaluates the production ContractLens retrieval pipeline against BM25.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd
from rank_bm25 import BM25Okapi
from tqdm import tqdm

# Ensure backend directory is in path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from backend.rag.pipeline import retrieve_top_sections

# -----------------------------------------------------------------------------
# 1. 50-Question Gold Standard Dataset
# -----------------------------------------------------------------------------
TEST_QUERIES = [
    {"query_id": "Q01", "query": "What constitutes fraud under the Indian Contract Act?", "gold_act": "contract_act", "gold_section": "17"},
    {"query_id": "Q02", "query": "Under which section is coercion defined in the Indian Contract Act?", "gold_act": "contract_act", "gold_section": "15"},
    {"query_id": "Q03", "query": "What constitutes undue influence according to the Indian Contract Act?", "gold_act": "contract_act", "gold_section": "16"},
    {"query_id": "Q04", "query": "How is misrepresentation defined under the Indian Contract Act?", "gold_act": "contract_act", "gold_section": "18"},
    {"query_id": "Q05", "query": "What defines free consent under the Indian Contract Act?", "gold_act": "contract_act", "gold_section": "14"},
    {"query_id": "Q06", "query": "Under which section is an agreement without consideration considered void?", "gold_act": "contract_act", "gold_section": "25"},
    {"query_id": "Q07", "query": "What constitutes an agreement in restraint of trade under the Contract Act?", "gold_act": "contract_act", "gold_section": "27"},
    {"query_id": "Q08", "query": "Under which section are wagering agreements declared void?", "gold_act": "contract_act", "gold_section": "30"},
    {"query_id": "Q09", "query": "What is a contingent contract under the Indian Contract Act?", "gold_act": "contract_act", "gold_section": "31"},
    {"query_id": "Q10", "query": "What makes an agreement void on ground of impossibility of act?", "gold_act": "contract_act", "gold_section": "56"},
    {"query_id": "Q11", "query": "What does Section 73 of the Contract Act cover regarding compensation for breach?", "gold_act": "contract_act", "gold_section": "73"},
    {"query_id": "Q12", "query": "How is compensation for breach where penalty is stipulated determined?", "gold_act": "contract_act", "gold_section": "74"},
    {"query_id": "Q13", "query": "What are the rights and responsibilities of a finder of goods?", "gold_act": "contract_act", "gold_section": "71"},
    {"query_id": "Q14", "query": "What defines a contract of indemnity under the Indian Contract Act?", "gold_act": "contract_act", "gold_section": "124"},
    {"query_id": "Q15", "query": "How is a contract of guarantee, surety, and principal debtor defined?", "gold_act": "contract_act", "gold_section": "126"},
    {"query_id": "Q16", "query": "What is a continuing guarantee and how is it defined?", "gold_act": "contract_act", "gold_section": "129"},
    {"query_id": "Q17", "query": "Under what section is bailment, bailor, and bailee defined?", "gold_act": "contract_act", "gold_section": "148"},
    {"query_id": "Q18", "query": "What is the standard duty of care required from a bailee?", "gold_act": "contract_act", "gold_section": "151"},
    {"query_id": "Q19", "query": "Under which section are agent and principal defined in the Contract Act?", "gold_act": "contract_act", "gold_section": "182"},
    {"query_id": "Q20", "query": "When is communication of acceptance complete against the proposer and acceptor?", "gold_act": "contract_act", "gold_section": "4"},
    {"query_id": "Q21", "query": "What is the punishment for criminal conspiracy under IPC?", "gold_act": "ipc", "gold_section": "120B"},
    {"query_id": "Q22", "query": "What constitutes sedition under the Indian Penal Code?", "gold_act": "ipc", "gold_section": "124A"},
    {"query_id": "Q23", "query": "How is unlawful assembly defined in the Indian Penal Code?", "gold_act": "ipc", "gold_section": "141"},
    {"query_id": "Q24", "query": "What is the punishment for rioting under the IPC?", "gold_act": "ipc", "gold_section": "147"},
    {"query_id": "Q25", "query": "Under which section is culpable homicide defined in the IPC?", "gold_act": "ipc", "gold_section": "299"},
    {"query_id": "Q26", "query": "What defines murder under the Indian Penal Code?", "gold_act": "ipc", "gold_section": "300"},
    {"query_id": "Q27", "query": "What is the punishment for murder under Section 302 of the IPC?", "gold_act": "ipc", "gold_section": "302"},
    {"query_id": "Q28", "query": "Under which section is dowry death punishable under the IPC?", "gold_act": "ipc", "gold_section": "304B"},
    {"query_id": "Q29", "query": "How is grievous hurt defined under the Indian Penal Code?", "gold_act": "ipc", "gold_section": "320"},
    {"query_id": "Q30", "query": "What is the punishment for voluntarily causing grievous hurt?", "gold_act": "ipc", "gold_section": "325"},
    {"query_id": "Q31", "query": "How is wrongful restraint defined in the Indian Penal Code?", "gold_act": "ipc", "gold_section": "339"},
    {"query_id": "Q32", "query": "How is wrongful confinement defined under Section 340 of the IPC?", "gold_act": "ipc", "gold_section": "340"},
    {"query_id": "Q33", "query": "How is theft defined under the Indian Penal Code?", "gold_act": "ipc", "gold_section": "378"},
    {"query_id": "Q34", "query": "What is the punishment for committing theft under IPC?", "gold_act": "ipc", "gold_section": "379"},
    {"query_id": "Q35", "query": "What constitutes extortion under the Indian Penal Code?", "gold_act": "ipc", "gold_section": "383"},
    {"query_id": "Q36", "query": "What constitutes robbery under Section 390 of the IPC?", "gold_act": "ipc", "gold_section": "390"},
    {"query_id": "Q37", "query": "What constitutes dacoity under the Indian Penal Code?", "gold_act": "ipc", "gold_section": "391"},
    {"query_id": "Q38", "query": "What is dishonest misappropriation of property under IPC?", "gold_act": "ipc", "gold_section": "403"},
    {"query_id": "Q39", "query": "How is criminal breach of trust defined under the IPC?", "gold_act": "ipc", "gold_section": "405"},
    {"query_id": "Q40", "query": "What constitutes cheating under Section 415 of the Indian Penal Code?", "gold_act": "ipc", "gold_section": "415"},
    {"query_id": "Q41", "query": "What constitutes forgery under the Indian Penal Code?", "gold_act": "ipc", "gold_section": "463"},
    {"query_id": "Q42", "query": "What is criminal intimidation defined under Section 503 IPC?", "gold_act": "ipc", "gold_section": "503"},
    {"query_id": "Q43", "query": "What does Article 14 of the Constitution of India guarantee?", "gold_act": "constitution", "gold_section": "14"},
    {"query_id": "Q44", "query": "Which Article prohibits discrimination on grounds of religion, race, caste, sex?", "gold_act": "constitution", "gold_section": "15"},
    {"query_id": "Q45", "query": "Which Article guarantees equality of opportunity in public employment?", "gold_act": "constitution", "gold_section": "16"},
    {"query_id": "Q46", "query": "Which Article of the Indian Constitution abolishes untouchability?", "gold_act": "constitution", "gold_section": "17"},
    {"query_id": "Q47", "query": "What fundamental freedoms are protected under Article 19 of the Constitution?", "gold_act": "constitution", "gold_section": "19"},
    {"query_id": "Q48", "query": "Which Article guarantees protection of life and personal liberty?", "gold_act": "constitution", "gold_section": "21"},
    {"query_id": "Q49", "query": "Which Article provides remedies for enforcement of fundamental rights?", "gold_act": "constitution", "gold_section": "32"},
    {"query_id": "Q50", "query": "Which Article provides for a Uniform Civil Code for citizens under DPSP?", "gold_act": "constitution", "gold_section": "44"},
]

# -----------------------------------------------------------------------------
# 2. Build BM25 Corpus from JSON Files
# -----------------------------------------------------------------------------
def load_raw_corpus() -> list[dict[str, str]]:
    """Loads all clauses from the 3 legal JSON files for BM25 baseline indexing."""
    data_dir = ROOT_DIR / "data" / "default"
    files = {
        "contract_act": "indian_contract_act_1872_cleaned.json",
        "ipc": "ipc.json",
        "constitution": "constitution_of_india.json",
    }
    corpus = []
    for act_key, filename in files.items():
        filepath = data_dir / filename
        if not filepath.exists():
            # Fallback if cleaned is not found
            if act_key == "contract_act":
                filepath = data_dir / "indian_contract_act_1872.json"
        
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError(f"Expected a JSON list in {filepath}")
                for item in data:
                    section = item.get("section_number", item.get("Section", item.get("article", "")))
                    text = item.get("text", item.get("section_desc", item.get("description", "")))
                    corpus.append({
                        "act": act_key,
                        "section": str(section).strip(),
                        "text": str(text or "").strip(),
                    })
    return corpus

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


ROMAN_VALUES = {
    "i": 1, "v": 5, "x": 10, "l": 50, "c": 100,
    "d": 500, "m": 1000,
}


def _roman_to_int(value: str) -> int | None:
    value = value.lower()
    if not value or any(char not in ROMAN_VALUES for char in value):
        return None
    total = 0
    previous = 0
    for char in reversed(value):
        current = ROMAN_VALUES[char]
        total += -current if current < previous else current
        previous = current
    return total


def _normalize_section(value: Any) -> set[str]:
    """Return equivalent forms for values such as ``Section 120-B`` and ``120B``."""
    raw = str(value or "").lower()
    raw = re.sub(r"\b(section|article|sec|art)\b", "", raw)
    compact = re.sub(r"[^a-z0-9]", "", raw)
    forms = {compact} if compact else set()
    for token in re.findall(r"\b[ivxlcdm]+\b|\b\d+[a-z]?\b", raw):
        roman = _roman_to_int(token)
        forms.add(str(roman) if roman is not None else token.replace("-", ""))
    return forms


def _normalize_act(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _act_aliases(gold_act: str) -> set[str]:
    normalized = _normalize_act(gold_act)
    if normalized in {"contractact", "indiancontractact"}:
        return {"contractact", "indiancontractact", "indiancontractact1872"}
    if normalized in {"ipc", "indianpenalcode"}:
        return {"ipc", "indianpenalcode", "indianpenalcode1860"}
    if normalized in {"constitution", "constitutionofindia"}:
        return {"constitution", "constitutionofindia"}
    return {normalized}


def _doc_payload(doc: Any) -> Mapping[str, Any]:
    if hasattr(doc, "payload"):
        return getattr(doc, "payload") or {}
    return doc if isinstance(doc, Mapping) else {}


def _doc_text(doc: Any) -> str:
    payload = _doc_payload(doc)
    return str(payload.get("text") or payload.get("clause_text") or getattr(doc, "text", "") or "")


def _doc_identity(doc: Any) -> str:
    payload = _doc_payload(doc)
    act = _normalize_act(payload.get("act") or getattr(doc, "act", ""))
    section = next(
        (value for value in (
            payload.get("section_number"), payload.get("section"), payload.get("article"),
            payload.get("clause_id"), payload.get("metadata", {}).get("section")
            if isinstance(payload.get("metadata"), Mapping) else None,
        ) if value not in (None, "")),
        "",
    )
    section_forms = sorted(_normalize_section(section))
    return f"{act}:{section_forms[0] if section_forms else str(getattr(doc, 'id', ''))}"


def is_hit(doc: Any, gold_act: str, gold_section: str) -> bool:
    """Match act/section metadata, including nested payloads and legal text headers."""
    payload = _doc_payload(doc)
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else {}
    act_values = [payload.get("act"), payload.get("source"), metadata.get("act")]
    section_values = [
        payload.get("section"), payload.get("article"), payload.get("clause_id"),
        payload.get("section_number"), metadata.get("section"), metadata.get("article"),
    ]
    text = _doc_text(doc)
    act_aliases = _act_aliases(gold_act)
    act_match = any(
        any(alias in _normalize_act(value) or _normalize_act(value) in act_aliases for alias in act_aliases)
        for value in act_values if value not in (None, "")
    )
    if not act_match:
        act_text = _normalize_act(text)
        act_match = any(alias in act_text for alias in act_aliases)

    gold_forms = _normalize_section(gold_section)
    section_match = any(gold_forms & _normalize_section(value) for value in section_values if value not in (None, ""))
    if not section_match:
        section_match = bool(re.search(
            rf"\b(?:section|sec\.?|article|art\.?)\s*{re.escape(str(gold_section))}\b",
            text,
            re.IGNORECASE,
        ))
    return act_match and section_match


def reciprocal_rank_fusion(
    dense_docs: list[Any],
    bm25_docs: list[dict[str, str]],
    k: int = 60,
    top_k: int = 5,
) -> list[tuple[Any, float, int | None, int | None]]:
    """Fuse the two ranked lists by canonical legal-document identity."""
    fused: dict[str, dict[str, Any]] = {}
    for rank, doc in enumerate(dense_docs, start=1):
        identity = _doc_identity(doc)
        entry = fused.setdefault(identity, {"doc": doc, "score": 0.0, "dense_rank": None, "bm25_rank": None})
        entry["score"] += 1.0 / (k + rank)
        entry["dense_rank"] = rank
    for rank, doc in enumerate(bm25_docs, start=1):
        identity = _doc_identity(doc)
        entry = fused.setdefault(identity, {"doc": doc, "score": 0.0, "dense_rank": None, "bm25_rank": None})
        entry["score"] += 1.0 / (k + rank)
        entry["bm25_rank"] = rank
        if entry["dense_rank"] is None:
            entry["doc"] = doc
    ranked = sorted(fused.values(), key=lambda entry: (-entry["score"], _doc_identity(entry["doc"])))
    return [(entry["doc"], entry["score"], entry["dense_rank"], entry["bm25_rank"]) for entry in ranked[:top_k]]

# -----------------------------------------------------------------------------
# 3. Main Evaluation Loop
# -----------------------------------------------------------------------------
def run_benchmark():
    print("================================================================")
    print(" Task 3: Benchmarking RAG Retrieval vs BM25 Baseline")
    print("================================================================\n")
    
    # Initialize BM25
    print("Loading corpus for BM25 Baseline...")
    raw_corpus = load_raw_corpus()
    if not raw_corpus:
        raise RuntimeError("No legal documents were loaded for the BM25 baseline.")
    tokenized_corpus = [tokenize(doc["text"]) for doc in raw_corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    print(f"BM25 Corpus indexed with {len(raw_corpus)} legal sections.\n")

    results_log = []
    
    metrics = {
        name: {"hits_1": 0, "hits_3": 0, "hits_5": 0, "rr_sum": 0.0}
        for name in ("dense", "bm25", "hybrid")
    }

    print("Running evaluation across 50 test questions...\n")
    for item in tqdm(TEST_QUERIES, desc="Evaluating Queries"):
        q_id = item["query_id"]
        query = item["query"]
        gold_act = item["gold_act"]
        gold_sec = item["gold_section"]

        dense_docs: list[Any] = []
        dense_error = ""
        try:
            # raw_top10 is the production dense Qdrant ranking. The optional
            # reranked list is deliberately excluded from this benchmark.
            retrieval = retrieve_top_sections(query=query, top_k_raw=10, top_k_final=5)
            dense_docs = list(retrieval.raw_top10[:10])
        except Exception as e:
            dense_error = f"{type(e).__name__}: {e}"
            print(f"Error executing dense retrieval for {q_id}: {dense_error}")

        bm25_docs: list[dict[str, str]] = []
        bm25_error = ""
        try:
            query_tokens = tokenize(query)
            bm25_scores = bm25.get_scores(query_tokens)
            top_10_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:10]
            bm25_docs = [raw_corpus[doc_idx] for doc_idx in top_10_indices]
        except Exception as e:
            bm25_error = f"{type(e).__name__}: {e}"
            print(f"Error executing BM25 retrieval for {q_id}: {bm25_error}")

        hybrid_docs = reciprocal_rank_fusion(dense_docs, bm25_docs, k=60, top_k=5)

        def first_hit(ranked_docs: list[Any]) -> int | None:
            for rank, doc in enumerate(ranked_docs, start=1):
                if is_hit(doc, gold_act, gold_sec):
                    return rank
            return None

        dense_rank = first_hit(dense_docs[:5])
        bm25_rank = first_hit(bm25_docs[:5])
        hybrid_rank = first_hit([entry[0] for entry in hybrid_docs])

        for name, rank in (("dense", dense_rank), ("bm25", bm25_rank), ("hybrid", hybrid_rank)):
            if rank is not None:
                metrics[name]["hits_1"] += rank <= 1
                metrics[name]["hits_3"] += rank <= 3
                metrics[name]["hits_5"] += rank <= 5
                metrics[name]["rr_sum"] += 1.0 / rank

        results_log.append({
            "query_id": q_id,
            "query": query,
            "gold_act": gold_act,
            "gold_section": gold_sec,
            "dense_rank": dense_rank if dense_rank else "Miss",
            "bm25_rank": bm25_rank if bm25_rank else "Miss",
            "hybrid_rank": hybrid_rank if hybrid_rank else "Miss",
            "dense_rr": (1.0 / dense_rank) if dense_rank else 0.0,
            "bm25_rr": (1.0 / bm25_rank) if bm25_rank else 0.0,
            "hybrid_rr": (1.0 / hybrid_rank) if hybrid_rank else 0.0,
            "dense_error": dense_error,
            "bm25_error": bm25_error,
        })

    # -------------------------------------------------------------------------
    # 4. Compute and Print Final Summary Table
    # -------------------------------------------------------------------------
    total_q = len(TEST_QUERIES)
    
    summary = {
        name: (
            metrics[name]["hits_1"] / total_q,
            metrics[name]["hits_3"] / total_q,
            metrics[name]["hits_5"] / total_q,
            metrics[name]["rr_sum"] / total_q,
        )
        for name in ("dense", "bm25", "hybrid")
    }

    print("\n================================================================")
    print(" Table 3: RAG Retrieval Quality vs Baseline (50 Test Questions)")
    print("================================================================")
    print("| Metric | Dense Qdrant | BM25 | Hybrid RRF |")
    print("|---|---:|---:|---:|")
    for label, index, multiplier in (
        ("Recall@1", 0, 100), ("Recall@3", 1, 100),
        ("Recall@5", 2, 100), ("MRR", 3, 1),
    ):
        suffix = "%" if multiplier == 100 else ""
        print(
            f"| {label} | {summary['dense'][index] * multiplier:.4f}{suffix} "
            f"| {summary['bm25'][index] * multiplier:.4f}{suffix} "
            f"| {summary['hybrid'][index] * multiplier:.4f}{suffix} |"
        )
    print(f"| Test questions | {total_q} | {total_q} | {total_q} |\n")

    # Save detailed outputs to CSV
    output_path = ROOT_DIR / "data" / "task3_rag_evaluation_results.csv"
    pd.DataFrame(results_log).to_csv(output_path, index=False)
    print(f"Detailed evaluation log saved to: {output_path}")

if __name__ == "__main__":
    run_benchmark()