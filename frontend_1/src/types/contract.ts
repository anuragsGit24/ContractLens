export interface Clause {
  index: number;
  label: string;
  text: string;
}

export interface GraphEdge {
  source_index: number;
  target_index: number;
  similarity: number;
}

export interface InternalContradiction {
  clause_a_index: number;
  clause_b_index: number;
  contradiction_score: number;
  relation: string;
}

export interface ClauseRisk {
  clause_index: number;
  top_category: string;
  top_score: number;
  category_scores: Record<string, number>;
  risk_level: 'high' | 'medium' | 'low' | string;
  risk_level_absolute?: string;
  risk_level_relative?: string;
}

export interface LawMatch {
  act: string;
  act_number: string;
  section_number: string;
  title: string;
  description: string;
  text: string;
  retrieval_score: number;
  rerank_score: number;
  contradiction_score: number;
}

export interface ClauseLawCheck {
  clause_index: number;
  law_matches: LawMatch[];
}

export interface CitationVerification {
  extracted_citations: string[];
  supported_citations: string[];
  unsupported_citations: string[];
  passed: boolean;
}

export interface ClauseExplanation {
  clause_index: number;
  explanation: string;
  prompt: string;
  citation_verification: CitationVerification;
  model_name: string;
  warning?: string | null;
}

export interface AnalyzeContractResponse {
  contract_path: string;
  clauses: Clause[];
  graph_edges: GraphEdge[];
  internal_contradictions: InternalContradiction[];
  risks: ClauseRisk[];
  law_checks: ClauseLawCheck[];
  explanations: ClauseExplanation[];
  placeholder_flags: Record<string, boolean>;
}

export interface UploadResponse {
  contract_id: string;
  file_name: string;
  stored_path: string;
  json_path: string;
}

export interface MetadataResponse {
  risk_categories: string[];
  qdrant_collection: string;
  payload_fields: string[];
  default_data_folder: string;
  users_data_folder: string;
  notes: string[];
}

export interface HealthResponse {
  status: string;
}

export interface AnalysisHistoryItem {
  id: string;
  fileName: string;
  timestamp: string;
  overallRisk: 'HIGH' | 'MEDIUM' | 'LOW';
  clauseCount: number;
  contradictionCount: number;
  result: AnalyzeContractResponse;
}

export interface AppSettings {
  fastMode: boolean;
  highThreshold: number;
  mediumThreshold: number;
}
