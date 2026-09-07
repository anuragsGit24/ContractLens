import type {
  AnalyzeContractResponse,
  HealthResponse,
  MetadataResponse,
  UploadResponse,
} from '../types/contract';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/v1';

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(4000) });
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function getMetadata(): Promise<MetadataResponse> {
  const res = await fetch(`${API_BASE}/metadata`, { signal: AbortSignal.timeout(4000) });
  if (!res.ok) throw new Error(`Failed to fetch metadata: ${res.statusText}`);
  return res.json();
}

export async function uploadContract(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/contracts/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }

  return res.json();
}

export interface AnalyzeParams {
  contractPath: string;
  fastMode: boolean;
  highThreshold: number;
}

export async function analyzeContract(params: AnalyzeParams): Promise<AnalyzeContractResponse> {
  const explainMax = params.fastMode ? 3 : 6;
  const lawMax = params.fastMode ? 8 : 14;

  const res = await fetch(`${API_BASE}/contracts/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contract_path: params.contractPath,
      explain_top_risks_only: params.fastMode,
      explain_max_clauses: explainMax,
      law_check_max_clauses: lawMax,
      explain_risk_threshold: params.highThreshold,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Contract analysis failed');
  }

  return res.json();
}
