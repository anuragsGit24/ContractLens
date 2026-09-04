import type { ClauseRisk } from '../types/contract';

export function getRiskLevel(score: number, highThreshold: number = 0.72, mediumThreshold: number = 0.58): 'HIGH' | 'MEDIUM' | 'LOW' {
  if (score >= highThreshold) return 'HIGH';
  if (score >= mediumThreshold) return 'MEDIUM';
  return 'LOW';
}

export function getOverallRisk(risks: ClauseRisk[], highThreshold: number = 0.72, mediumThreshold: number = 0.58): 'HIGH' | 'MEDIUM' | 'LOW' {
  if (!risks || risks.length === 0) return 'LOW';
  const hasHigh = risks.some(r => r.top_score >= highThreshold);
  if (hasHigh) return 'HIGH';
  const hasMedium = risks.some(r => r.top_score >= mediumThreshold);
  if (hasMedium) return 'MEDIUM';
  return 'LOW';
}

export function getActShortName(act: string): string {
  const norm = (act || '').toLowerCase();
  if (norm.includes('contract')) return 'ICA';
  if (norm.includes('penal') || norm === 'ipc') return 'IPC';
  if (norm.includes('constitution')) return 'CONST';
  return act.slice(0, 5).toUpperCase();
}

export function truncateText(text: string, maxLen: number = 90): string {
  if (!text) return '';
  const clean = text.replace(/\s+/g, ' ').trim();
  return clean.length > maxLen ? `${clean.slice(0, maxLen)}...` : clean;
}

export interface ParsedExplanation {
  riskSummary: string;
  whyRisky: string;
  practicalImpact: string;
  rewrite: string;
  citations: string;
}

const SECTION_HEADERS = [
  { key: 'riskSummary', regex: /^(?:\d[\)\.:\-]\s*)?risk\s*summary\s*[:\-]?\s*(.*)$/i },
  { key: 'whyRisky', regex: /^(?:\d[\)\.:\-]\s*)?why\s*risky(?:\s*under\s*indian\s*law)?\s*[:\-]?\s*(.*)$/i },
  { key: 'practicalImpact', regex: /^(?:\d[\)\.:\-]\s*)?practical\s*impact(?:\s*on\s*business)?\s*[:\-]?\s*(.*)$/i },
  { key: 'rewrite', regex: /^(?:\d[\)\.:\-]\s*)?safer\s*rewrite\s*suggestion\s*[:\-]?\s*(.*)$/i },
  { key: 'citations', regex: /^(?:\d[\)\.:\-]\s*)?citations?\s*[:\-]?\s*(.*)$/i },
];

export function parseExplanation(raw: string): ParsedExplanation {
  const result: Record<string, string[]> = {
    riskSummary: [],
    whyRisky: [],
    practicalImpact: [],
    rewrite: [],
    citations: [],
  };

  let current = 'riskSummary';
  const lines = (raw || '').split('\n');

  for (const line of lines) {
    const clean = line.replace(/[`*_#]/g, '').trim();
    if (!clean) continue;

    let matched = false;
    for (const h of SECTION_HEADERS) {
      const m = clean.match(h.regex);
      if (m) {
        current = h.key;
        if (m[1] && m[1].trim()) {
          result[current].push(m[1].trim());
        }
        matched = true;
        break;
      }
    }

    if (!matched) {
      result[current].push(clean);
    }
  }

  return {
    riskSummary: result.riskSummary.join('\n').trim() || raw,
    whyRisky: result.whyRisky.join('\n').trim(),
    practicalImpact: result.practicalImpact.join('\n').trim(),
    rewrite: result.rewrite.join('\n').trim(),
    citations: result.citations.join('\n').trim(),
  };
}
