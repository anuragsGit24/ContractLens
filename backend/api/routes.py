from __future__ import annotations

import shutil
import uuid
from pathlib import Path
import pandas as pd
import io
import networkx as nx
from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.core.config import get_settings
from backend.core.constants import RISK_CATEGORIES
from backend.core.model_registry import get_qdrant_client
from backend.schemas.contracts import (
    AnalyzeContractRequest,
    AnalyzeContractResponse,
    BuildGraphRequest,
    BuildGraphResponse,
    ExplainRequest,
    FindContradictionsRequest,
    FindContradictionsResponse,
    LawCheckRequest,
    LawCheckResponse,
    MetadataResponse,
    PlaceholderResponse,
    RiskRequest,
    RiskResponse,
    UploadResponse,
)
from backend.services.dynamic_graph_builder import build_dynamic_graph 
from backend.services.analyzer import analyze_contract
from backend.services.document_graph import build_document_graph, find_internal_contradictions
from backend.services.document_parser import extract_clauses
from backend.services.law_checker import check_against_law
from backend.services.llm_explainer import explain_clause
from backend.services.risk_scorer import score_all_clauses

router = APIRouter(prefix="/v1", tags=["contractlens"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metadata", response_model=MetadataResponse)
def metadata() -> MetadataResponse:
    settings = get_settings()
    return MetadataResponse(
        risk_categories=RISK_CATEGORIES,
        qdrant_collection=settings.qdrant_collection,
        payload_fields=["act", "section_number", "title", "text"],
        default_data_folder=str(settings.default_data_dir),
        users_data_folder=str(settings.users_data_dir),
        notes=[
            "Default legal corpora stay in data/default.",
            "Uploaded contracts are stored in data/users/contracts.",
            "Document graph is in-memory per analysis run.",
        ],
    )


@router.get("/qdrant/health")
def qdrant_health() -> dict:
    settings = get_settings()
    if not settings.qdrant_api_key:
        return {
            "status": "error",
            "qdrant_url": settings.qdrant_url,
            "collection": settings.qdrant_collection,
            "api_key_configured": False,
            "message": "QDRANT_API_KEY is missing. Add it in backend/.env or environment variables.",
        }

    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        names = [c.name for c in collections]
        return {
            "status": "ok",
            "qdrant_url": settings.qdrant_url,
            "collection": settings.qdrant_collection,
            "api_key_configured": True,
            "collection_exists": settings.qdrant_collection in names,
            "collections_count": len(names),
        }
    except Exception as exc:
        return {
            "status": "error",
            "qdrant_url": settings.qdrant_url,
            "collection": settings.qdrant_collection,
            "api_key_configured": True,
            "message": str(exc),
        }


@router.post("/contracts/upload", response_model=UploadResponse)
def upload_contract(file: UploadFile = File(...)) -> UploadResponse:
    settings = get_settings()

    suffix = Path(file.filename or "uploaded.pdf").suffix.lower()
    if suffix != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    contract_id = str(uuid.uuid4())
    safe_name = Path(file.filename or "contract.pdf").name.replace(" ", "_")
    target = settings.user_contracts_dir / f"{contract_id}_{safe_name}"

    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    return UploadResponse(contract_id=contract_id, file_name=safe_name, stored_path=str(target))


@router.post("/contracts/parse")
def parse_contract(payload: dict[str, str]) -> dict:
    contract_path = payload.get("contract_path", "")
    if not contract_path:
        raise HTTPException(status_code=400, detail="contract_path is required")
    clauses = extract_clauses(contract_path)
    return {"contract_path": contract_path, "clauses": [c.model_dump() for c in clauses]}


@router.post("/contracts/document-graph", response_model=BuildGraphResponse)
def document_graph(req: BuildGraphRequest) -> BuildGraphResponse:
    # 🔹 Step 1: build graph
    G = build_dynamic_graph("\n".join(req.clauses))
    # 🔹 Step 2: extract nodes
    nodes = [G.nodes[n]["text"] for n in G.nodes]
    # 🔹 Step 3: extract edges (ONLY risk)
    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "risk": data.get("risk", 0)
        })
    return BuildGraphResponse(
        nodes=nodes,
        edges=edges
    )


@router.post("/contracts/internal-contradictions", response_model=FindContradictionsResponse)
def internal_contradictions(req: FindContradictionsRequest) -> FindContradictionsResponse:
    contradictions = find_internal_contradictions(
        clauses=req.clauses,
        edges=req.edges,
        contradiction_threshold=req.contradiction_threshold,
    )
    return FindContradictionsResponse(contradictions=contradictions)


@router.post("/contracts/risk-score", response_model=RiskResponse)
def risk_score(req: RiskRequest) -> RiskResponse:
    return RiskResponse(risks=score_all_clauses(req.clauses))


@router.post("/contracts/law-check", response_model=LawCheckResponse)
def law_check(req: LawCheckRequest) -> LawCheckResponse:
    results = check_against_law(
        clauses=req.clauses,
        clause_vectors=req.clause_vectors,
        top_k_raw=req.top_k_raw,
        top_k_final=req.top_k_final,
        contradiction_threshold=req.contradiction_threshold,
    )
    return LawCheckResponse(results=results)


@router.post("/contracts/explain")
def explain(req: ExplainRequest) -> dict:
    explanation = explain_clause(
        clause=req.clause,
        risk=req.risk,
        contradictions=req.contradictions,
        law_matches=req.law_matches,
    )
    return explanation.model_dump()


@router.post("/contracts/analyze", response_model=AnalyzeContractResponse)
def analyze(req: AnalyzeContractRequest) -> AnalyzeContractResponse:
    path = Path(req.contract_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Contract not found: {path}")

    return analyze_contract(
        contract_path=path,
        similarity_threshold=req.similarity_threshold,
        contradiction_threshold=req.contradiction_threshold,
        top_k_raw=req.top_k_raw,
        top_k_final=req.top_k_final,
        explain_top_risks_only=req.explain_top_risks_only,
        explain_risk_threshold=req.explain_risk_threshold,
    )


@router.get("/contracts/law-graph/status", response_model=PlaceholderResponse)
def law_graph_status() -> PlaceholderResponse:
    return PlaceholderResponse(
        feature="law_graph",
        implemented=False,
        message="Law graph is intentionally deferred. Qdrant retrieval is the active path.",
        details={"priority": "low", "planned_output": "legal_graph.pkl"},
    )
