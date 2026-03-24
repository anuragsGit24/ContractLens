# ContractLens Performance Changelog (2026-03-24)

## Purpose
This document explains how end-to-end runtime dropped from ~5-10 minutes to ~15-20 seconds for typical runs, and lists all code changes currently present in the working tree since the last pull.

It is written for handoff to teammates:
- What changed
- Why it changed
- What impact you should expect
- Any side effects or trade-offs

## Executive Summary
Latency reduced by removing repeated heavy model loads, replacing NLI/zero-shot/cross-encoder calls with fast cosine/rule logic, and bounding expensive pipeline stages (especially law checks + explanations). We also fixed parsing/segmentation behavior that inflated clause counts and made graph complexity explode.

Primary latency wins came from:
1. Single model singleton (InLegalBERT) loaded once at startup.
2. Replacing per-request auxiliary models (NLI, zero-shot, reranker).
3. Capping expensive steps (law-check clauses, explanations).
4. Reusing already-computed embeddings (avoid duplicate passes).
5. OCR and parsing optimizations to avoid oversized clause sets.
6. Fast-fail behavior for unavailable external services (Ollama/Qdrant timeout controls).

---

## A. Model Lifecycle and Inference Architecture

### 1) New singleton model loader
File: `backend/services/model_singleton.py`

What changed:
- Added one global `SentenceTransformer("law-ai/InLegalBERT")` instance.
- Added helper functions `embed(...)` and `embed_single(...)`.

Why:
- Prevent model construction inside request-time functions.
- Avoid repeated disk/network/model-init overhead.

Impact:
- Model loads once at process startup, then reused.
- Stabilizes latency and memory profile.

Trade-off:
- Slightly longer startup time, much faster request time.

### 2) Startup warmup imports
File: `backend/main.py`

What changed:
- Import of `model_singleton` and `risk_scorer` at startup.

Why:
- Force one-time initialization early (model + risk vectors).

Impact:
- First user request avoids cold-start model initialization.

### 3) Removed old model registry paths
Files:
- `backend/core/model_registry.py`
- `backend/core/config.py`

What changed:
- Removed NLI / zero-shot / reranker model config fields and builders.
- Kept embedding adapter around singleton for compatibility.
- Added Qdrant client timeout (`timeout=8`).

Why:
- Enforce one-model policy.
- Avoid slow/stuck network calls from accumulating.

Impact:
- Fewer model dependencies and fewer accidental heavy calls.
- Faster failover on slow Qdrant conditions.

---

## B. Contradiction Detection Pipeline

### 4) Replaced NLI with rules + cosine
File: `backend/services/contradiction_detector.py` (new)

What changed:
- Added positive/negative obligation regex logic.
- Added a fallback path for subtle conflicts: if similarity is in 0.72-0.89 and both clauses share legal-subject keywords (seller, buyer, liability, quality, etc.), mark as possible tension even without polarity mismatch.
- Contradiction confidence now uses two tiers: high confidence for polarity mismatch, lower confidence for shared-subject tension.

Why:
- NLI model was costly and unnecessary for latency target.

Impact:
- Near-constant-time contradiction logic after embeddings are available.

### 5) Document graph contradiction logic rewrite
File: `backend/services/document_graph.py`

What changed:
- Removed NLI pipeline usage.
- Added vectorized similarity matrix computation (`mat @ mat.T`).
- Added edge candidate limits (`max_pairs`) and conflict-zone candidate strategy.
- Added fallback candidate selection when all similarities are high.
- Added tension threshold handling.

Why:
- Reduce Python-loop overhead and align candidate selection with new detector behavior.

Impact:
- Contradiction stage much faster and no model pipeline dependency.
- Better chance of non-empty contradiction output on compacted OCR text.

Trade-off:
- Heuristic-based contradictions are less semantically rich than a full NLI model.

---

## C. Law Matching and Reranking

### 6) Replaced cross-encoder reranker
Files:
- `backend/services/reranker.py` (new)
- `backend/rag/reranker.py`

What changed:
- Rerank now uses cosine similarity on normalized InLegalBERT embeddings.
- `CrossEncoderReranker` compatibility class now wraps embedding dot-product behavior.

Why:
- Cross-encoder inference was expensive and caused request-time latency spikes.

Impact:
- Faster reranking with a single embedding model.

### 7) Law checker optimization and bounding
File: `backend/services/law_checker.py`

What changed:
- Removed NLI and cross-encoder dependencies.
- Added one-shot embedding of unique retrieved law snippets.
- Replaced repeated per-clause per-hit embedding loops.
- Added try/except fail-open around retrieval calls.
- Uses contradiction detector logic for clause-vs-law conflict scoring.

Why:
- This was a major bottleneck at scale.

Impact:
- Significant reduction in law-check stage runtime.
- Better resilience when retrieval intermittently fails.

Trade-off:
- On retrieval failure, returns fewer law matches instead of blocking the whole request.

### 8) RAG embedding plumbing redirected to singleton
Files:
- `backend/rag/embeddings.py`
- `backend/rag/pipeline.py`

What changed:
- RAG embedder uses singleton backend embedder.
- Reranker model default shifted to singleton-compatible value.

Why:
- Remove accidental secondary model load paths.

Impact:
- Consistent model behavior across services.

---

## D. Risk Scoring

### 9) Removed zero-shot classifier
File: `backend/services/risk_scorer.py`

What changed:
- Replaced zero-shot pipeline with cosine scoring against pre-embedded risk category descriptions.
- Added precomputed risk vectors at module import.

Why:
- Zero-shot model (e.g., bart-large-mnli) was heavy and slow.

Impact:
- Risk scoring now fast vector math.

### 10) Reused clause embeddings to avoid duplicate work
Files:
- `backend/services/risk_scorer.py`
- `backend/services/analyzer.py`

What changed:
- `score_all_clauses` accepts optional precomputed vectors.
- Analyzer passes document-graph vectors into risk scoring.

Why:
- Remove redundant full embedding pass.

Impact:
- Reduced total compute time for large documents.

### 11) Risk level calibration changes
File: `backend/services/risk_scorer.py`

What changed:
- Risk levels now use absolute score thresholds as the primary signal (`high >= 0.72`, `medium >= 0.58`, else `low`).
- Relative calibration is retained only as secondary metadata (`risk_level_relative`) so ranking context is preserved without overriding absolute risk labels.

Why:
- Keep user-facing risk labels stable and document-faithful while still providing distribution context.

Impact:
- Risk labels now reflect intrinsic clause risk first, independent of document size/distribution.
- Relative context is still available for downstream UI/explanation layers.

Trade-off:
- Outputs now include two risk labels (`risk_level_absolute` and `risk_level_relative`) which adds a small amount of response verbosity.

---

## E. Analyzer Orchestration and Budgeting

### 12) Added stage-level timing instrumentation
File: `backend/services/analyzer.py`

What changed:
- Added timing logs for parse, graph, contradiction, risk, law-check, explain, total.

Why:
- Make bottlenecks visible in production-like runs.

Impact:
- Easier debugging and performance regression detection.

### 13) Added bounded work controls
Files:
- `backend/services/analyzer.py`
- `backend/schemas/contracts.py`
- `backend/api/routes.py`

What changed:
- New request controls: `explain_max_clauses`, `law_check_max_clauses`.
- Defaults set to fast mode (`explain_max_clauses=0`, law checks limited).

Why:
- Control worst-case latency on long contracts.

Impact:
- Predictable response times and fewer timeouts.

Trade-off:
- Deep analysis is intentionally partial unless caller raises limits.

---

## F. Parsing and Clause Volume Control

### 14) Parser supports JSON contracts directly
File: `backend/services/document_parser.py`

What changed:
- Added `.json` parsing path for uploaded OCR output.

Why:
- Avoid re-parsing PDF text when OCR JSON already exists.

Impact:
- Faster analysis startup and simpler data path.

### 15) Clause compaction and cap
File: `backend/services/document_parser.py`

What changed:
- Added `_compact_clause_texts(...)` to merge short fragments and cap clause count.

Why:
- OCR-generated fragments can explode clause count and graph complexity.

Impact:
- Reduced clause count, controlled graph size, improved runtime.

Trade-off:
- Coarser clause segmentation may blur some fine-grained structure.

---

## G. OCR Upload Path Optimization

### 16) OCR performance tuning without changing flow
File: `backend/services/pdf_to_ocr.py`

What changed:
- Added configurable OCR knobs:
  - `OCR_DPI` (default 220)
  - `OCR_THREADS`
  - `OCR_LANG`
  - `OCR_PSM` (default 6)
  - `OCR_OEM` (default 1)
- Enabled grayscale rendering + thread_count in Poppler conversion.
- Switched string concatenation to list-join.

Why:
- Upload endpoint does OCR inline; this was the main upload-time bottleneck.

Impact:
- Noticeably faster upload completion for large PDFs.

Trade-off:
- Lower DPI can slightly reduce OCR fidelity on poor scans.

### 17) Upload response includes generated JSON path
Files:
- `backend/api/routes.py`
- `backend/schemas/contracts.py`

What changed:
- Upload returns `json_path` and writes OCR clauses to JSON.

Why:
- Allows downstream analysis to consume preprocessed text directly.

Impact:
- Fewer repeated expensive steps in frontend/backend flow.

---

## H. Frontend Workflow and UX

### 18) Removed duplicate heavy backend calls
File: `frontend/app.py`

What changed:
- Frontend no longer always calls separate parse + graph after analyze.
- Graph display now derived from analyze response payload.

Why:
- Duplicate calls re-ran expensive stages.

Impact:
- Lower total waiting time and fewer timeout risks.

### 19) Fast-mode request defaults
File: `frontend/app.py`

What changed:
- Analyze request includes:
  - `explain_max_clauses=0`
  - `law_check_max_clauses=8`
- Upload timeout increased to 180s.
- Analyze timeout set to 180s.

Why:
- Keep UI responsive for large files.

Impact:
- Less likely to hit frontend read timeouts.

### 20) Better empty-state messaging
File: `frontend/app.py`

What changed:
- Explicit info messages when no high-risk or no contradiction items are returned.
- Added risk summary caption (high/medium/total).

Why:
- Avoid confusion between "blank due to bug" vs "no items under thresholds".

Impact:
- Better trust and interpretability for users.

---

## I. Miscellaneous / Maintenance

### 21) Dynamic graph builder moved off all-MiniLM
File: `backend/services/dynamic_graph_builder.py`

What changed:
- Uses singleton embeddings instead of separate SentenceTransformer load.

Why:
- Keep one-model policy and avoid hidden model initialization.

Impact:
- Consistent inference stack.

### 22) Cleanup comment references
File: `backend/scripts/base_graph_builder.py`

What changed:
- Removed stale all-MiniLM comment.

Impact:
- Reduces confusion for maintainers.

### 23) Dependencies/readme updates
Files:
- `backend/requirements.txt`
- `backend/README.md`

What changed:
- Added/adjusted packages and Windows OCR setup notes.

Impact:
- Easier environment setup and consistent local behavior.

---

## J. Important Current Repository State Note
`git status` currently shows `backend/api/routes.py` in conflict state (`UU`).

What this means:
- There are unresolved merge markers/history around this file in the current tree.
- Before any production deployment or release branch cut, resolve that conflict cleanly.

Why it matters for latency docs:
- Several key performance controls are wired through analyze route parameters.
- A bad conflict resolution here can silently drop optimization flags.

---

## Recommended Runtime Settings (Large PDF Defaults)
Use these defaults for practical speed while keeping analysis quality reasonable:

- Analyze request:
  - `explain_max_clauses=0`
  - `law_check_max_clauses=8`
- OCR env:
  - `OCR_DPI=220` (or 180 for max speed)
  - `OCR_THREADS=<cpu_cores_minus_1>`
  - `OCR_PSM=6`
  - `OCR_OEM=1`

---

## Before/After Behavior (Observed)
Typical observed outcomes during tuning iterations:
- Before: cold requests + repeated heavy model/pipeline stages + oversized clause counts often led to multi-minute latency.
- After: one model in memory, bounded heavy stages, vectorized math, and parser/OCR controls brought many runs into sub-30s territory, with representative runs around ~15-20s depending on document/host load.

---

## Teammate FAQ

### Why can startup still look "heavy" in logs?
Model loads once at process start. That is expected and intentional.

### Why are some deep features reduced by default?
Fast-mode defaults are chosen to prevent timeouts for large contracts. You can raise limits per request when needed.

### Why did risk labels change?
Risk labeling is now absolute-first (fixed thresholds), with relative calibration exposed separately as contextual metadata.

### What is the biggest remaining cost now?
For large contracts, graph pairwise similarity and OCR remain dominant costs. Both are now bounded/tuned but still data-size dependent.

---

## Change Inventory (from current working tree)
Performance-critical files touched:
- `backend/services/model_singleton.py`
- `backend/main.py`
- `backend/core/model_registry.py`
- `backend/core/config.py`
- `backend/services/document_graph.py`
- `backend/services/contradiction_detector.py`
- `backend/services/law_checker.py`
- `backend/services/risk_scorer.py`
- `backend/services/analyzer.py`
- `backend/services/document_parser.py`
- `backend/services/llm_explainer.py`
- `backend/services/pdf_to_ocr.py`
- `backend/rag/embeddings.py`
- `backend/rag/reranker.py`
- `backend/rag/pipeline.py`
- `backend/schemas/contracts.py`
- `backend/api/routes.py`
- `frontend/app.py`

Other touched files (setup/docs/support):
- `backend/requirements.txt`
- `backend/README.md`
- `backend/services/TextToCsv.py`
- `backend/services/dynamic_graph_builder.py`
- `backend/scripts/base_graph_builder.py`

---

## Suggested Team Next Step
Create a "Fast vs Deep" analysis mode toggle in frontend so product users can choose:
- Fast: bounded checks, no explanations (default)
- Deep: larger law-check budget + explanations for final legal review
