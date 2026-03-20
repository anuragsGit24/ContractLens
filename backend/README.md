# ContractLens Backend

This backend is organized for team development with clear service boundaries.

## Run

```bash
uvicorn backend.main:app --reload
```

API docs are at `/docs`.

## Structure

- `backend/main.py`: FastAPI app entrypoint
- `backend/api/routes.py`: REST endpoints for each pipeline stage
- `backend/core/config.py`: environment and path settings
- `backend/core/model_registry.py`: singleton loaders for heavy models
- `backend/schemas/contracts.py`: request and response contracts (Pydantic)
- `backend/services/document_parser.py`: PDF to clause extraction
- `backend/services/document_graph.py`: graph build + internal contradiction detection
- `backend/services/risk_scorer.py`: zero-shot risk scoring
- `backend/services/law_checker.py`: clause-vs-law retrieval and contradiction checks
- `backend/services/llm_explainer.py`: prompt build, Ollama call, citation verification
- `backend/services/analyzer.py`: full end-to-end orchestration

## Data Contract

### Static legal corpus

- folder: `data/default`
- source files: Constitution, IPC, Contract Act JSONs
- vector store: Qdrant collection `contractlens_legal`
- payload fields: `act`, `section_number`, `title`, `text`

### User contracts

- upload destination: `data/users/contracts`
- one file per upload: `{contract_id}_{filename}.pdf`
- contracts are used for in-memory analysis; no user contract vectors are persisted in Qdrant by default

## Endpoints Summary

- `GET /v1/health`
- `GET /v1/metadata`
- `POST /v1/contracts/upload`
- `POST /v1/contracts/parse`
- `POST /v1/contracts/document-graph`
- `POST /v1/contracts/internal-contradictions`
- `POST /v1/contracts/risk-score`
- `POST /v1/contracts/law-check`
- `POST /v1/contracts/explain`
- `POST /v1/contracts/analyze`
- `GET /v1/contracts/law-graph/status` (placeholder)

## Placeholders

The law graph (cross-referenced statute graph) is intentionally marked as not implemented.

## Excalidraw Link: 
https://excalidraw.com/#room=72efef27cd48eb04f08a,8Hu6jhOu09rDDXJ-l9p-hA
