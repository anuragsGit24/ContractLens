from __future__ import annotations

from typing import Any, List, Optional, Dict

from pydantic import BaseModel, Field


class Clause(BaseModel):
    index: int
    label: str
    text: str


class ClauseWithVector(Clause):
    embedding: list[float] | None = None


class GraphEdge(BaseModel):
    source_index: int
    target_index: int
    similarity: float


class InternalContradiction(BaseModel):
    clause_a_index: int
    clause_b_index: int
    contradiction_score: float
    relation: str = "CONTRADICTION"


class ClauseRisk(BaseModel):
    clause_index: int
    top_category: str
    top_score: float
    category_scores: dict[str, float]
    risk_level: str
    risk_level_absolute: str | None = None
    risk_level_relative: str | None = None


class LawMatch(BaseModel):
    act: str
    act_number: str
    section_number: str
    title: str
    description: str
    text: str
    retrieval_score: float
    rerank_score: float
    contradiction_score: float


class ClauseLawCheck(BaseModel):
    clause_index: int
    law_matches: list[LawMatch]


class CitationVerification(BaseModel):
    extracted_citations: list[str]
    supported_citations: list[str]
    unsupported_citations: list[str]
    passed: bool


class ClauseExplanation(BaseModel):
    clause_index: int
    explanation: str
    prompt: str
    citation_verification: CitationVerification
    model_name: str
    warning: str | None = None


class BuildGraphRequest(BaseModel):
    clauses: list[str]

class NodeOut(BaseModel):
    id: int
    text: str


class EdgeOut(BaseModel):
    source: int
    target: int
    risk: float
    difference: float | None = None   # optional but useful
    base_nodes: dict | None = None    # optional for explainability


class BuildGraphResponse(BaseModel):
    nodes: list[NodeOut]
    edges: list[EdgeOut]


class FindContradictionsRequest(BaseModel):
    clauses: list[Clause]
    edges: list[GraphEdge]
    contradiction_threshold: float = Field(default=0.68, ge=0.0, le=1.0)


class FindContradictionsResponse(BaseModel):
    contradictions: list[InternalContradiction]


class RiskRequest(BaseModel):
    clauses: list[Clause]


class RiskResponse(BaseModel):
    risks: list[ClauseRisk]


class LawCheckRequest(BaseModel):
    clauses: list[Clause]
    clause_vectors: list[list[float]] | None = None
    top_k_raw: int = Field(default=10, ge=1, le=50)
    top_k_final: int = Field(default=3, ge=1, le=20)
    contradiction_threshold: float = Field(default=0.68, ge=0.0, le=1.0)


class LawCheckResponse(BaseModel):
    results: list[ClauseLawCheck]


class ExplainRequest(BaseModel):
    clause: Clause
    risk: ClauseRisk
    contradictions: list[InternalContradiction] = Field(default_factory=list)
    law_matches: list[LawMatch] = Field(default_factory=list)


class AnalyzeContractRequest(BaseModel):
    """
    Full contract analysis request with Fast Mode + threshold control.
    
    Fast Mode settings:
    - explain_max_clauses: Higher value (6+) for deeper analysis, lower (3) for fast mode
    - law_check_max_clauses: Higher value (14+) for thorough checking, lower (8) for fast mode
    """
    contract_path: str
    similarity_threshold: float = Field(default=0.75, ge=0.0, le=1.0, description="Graph edge creation threshold")
    contradiction_threshold: float = Field(default=0.68, ge=0.0, le=1.0, description="Contradiction detection threshold")
    top_k_raw: int = Field(default=10, ge=1, le=50, description="Raw retrieval candidates from Qdrant")
    top_k_final: int = Field(default=3, ge=1, le=20, description="Final law matches per clause")
    explain_top_risks_only: bool = Field(default=True, description="Only explain clauses above explain_risk_threshold")
    explain_risk_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Risk score floor for explanation (user-configurable)")
    explain_max_clauses: int = Field(default=3, ge=0, le=50, description="Max clauses to generate explanations for (Fast Mode: 3, Full: 6)")
    law_check_max_clauses: int = Field(default=8, ge=0, le=500, description="Max clauses to check against law (Fast Mode: 8, Full: 14)")


class AnalyzeContractResponse(BaseModel):
    contract_path: str
    clauses: list[Clause]
    graph_edges: list[GraphEdge]
    internal_contradictions: list[InternalContradiction]
    risks: list[ClauseRisk]
    law_checks: list[ClauseLawCheck]
    explanations: list[ClauseExplanation]
    placeholder_flags: dict[str, bool]


class UploadResponse(BaseModel):
    contract_id: str
    file_name: str
    stored_path: str
    json_path: str

class MetadataResponse(BaseModel):
    risk_categories: list[str]
    qdrant_collection: str
    payload_fields: list[str]
    default_data_folder: str
    users_data_folder: str
    notes: list[str]


class PlaceholderResponse(BaseModel):
    feature: str
    implemented: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
