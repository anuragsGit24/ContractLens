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
    NodeOut,
    EdgeOut
)
from backend.services.dynamic_graph_builder import build_dynamic_graph 
from backend.services.analyzer import analyze_contract
from backend.services.document_graph import build_document_graph, find_internal_contradictions
from backend.services.document_parser import extract_clauses
from backend.services.law_checker import check_against_law
from backend.services.llm_explainer import explain_clause
from backend.services.risk_scorer import score_all_clauses
from backend.services.pdf_to_ocr import PDFtoOCR
from backend.services.pdf_to_ocr import PDFtoOCR # you need to wrap your script into function
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

@router.post("/contracts/upload", response_model=UploadResponse)
def upload_contract(file: UploadFile = File(...)) -> UploadResponse:
    settings = get_settings()

    suffix = Path(file.filename or "uploaded.pdf").suffix.lower()
    if suffix != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    settings.user_contracts_dir.mkdir(parents=True, exist_ok=True)

    contract_id = str(uuid.uuid4())
    safe_name = Path(file.filename or "contract.pdf").name.replace(" ", "_")
    target = settings.user_contracts_dir / f"{contract_id}_{safe_name}"

    # save PDF
    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        ocr = PDFtoOCR()
        clauses = ocr.pdf_to_json(str(target))
        # save JSON
        json_path = target.with_suffix(".json")

        # ✅ FIX 2: safe JSON write
        import json
        with json_path.open("w", encoding="utf-8") as f:
            json.dump({"clauses": clauses}, f, indent=2, ensure_ascii=False)

    except Exception as e:
        import traceback
        print(traceback.format_exc())   # 👈 prints full error in terminal
        raise HTTPException(status_code=500, detail=str(e))

    return UploadResponse(
        contract_id=contract_id,
        file_name=safe_name,
        stored_path=str(target),
        json_path=str(json_path)
    )


@router.post("/contracts/parse")
def parse_contract(payload: dict[str, str]) -> dict:
    contract_path = payload.get("contract_path", "")
    if not contract_path:
        raise HTTPException(status_code=400, detail="contract_path is required")
    clauses = extract_clauses(contract_path)
    return {"contract_path": contract_path, "clauses": [c.model_dump() for c in clauses]}


@router.post("/contracts/document-graph", response_model=BuildGraphResponse)
def document_graph(req: BuildGraphRequest) -> BuildGraphResponse:

    clauses = req.clauses  # ✅ already list[str]

    G = build_dynamic_graph("\n".join(clauses))

    nodes = [
        NodeOut(id=n, text=G.nodes[n]["text"])
        for n in G.nodes
    ]

    edges = [
        EdgeOut(
            source=u,
            target=v,
            risk=float(data.get("risk", 0)),
            difference=data.get("difference"),
            base_nodes=data.get("base_nodes")
        )
        for u, v, data in G.edges(data=True)
    ]

    return BuildGraphResponse(nodes=nodes, edges=edges)

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
