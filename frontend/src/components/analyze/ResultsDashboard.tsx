import React, { useState } from 'react';
import { 
  ArrowLeft, 
  Download, 
  Printer, 
  Share2, 
  Check
} from 'lucide-react';
import type { AnalyzeContractResponse } from '../../types/contract';
import { getOverallRisk, getRiskLevel } from '../../utils/formatters';
import { RiskBanner } from './RiskBanner';
import { MetricCards } from './MetricCards';
import { RiskMeter } from './RiskMeter';
import { KnowledgeGraph } from './KnowledgeGraph';
import { ClauseMatrix } from './ClauseMatrix';
import { ContradictionCards } from './ContradictionCards';
import { LawMatches } from './LawMatches';
import { AIExplainer } from './AIExplainer';

interface ResultsDashboardProps {
  result: AnalyzeContractResponse;
  fileName?: string;
  highThreshold: number;
  mediumThreshold: number;
  onReset: () => void;
}

export const ResultsDashboard: React.FC<ResultsDashboardProps> = ({
  result,
  fileName,
  highThreshold,
  mediumThreshold,
  onReset,
}) => {
  const [selectedClauseId, setSelectedClauseId] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);

  const overallRisk = getOverallRisk(result.risks, highThreshold, mediumThreshold);

  let highCount = 0;
  let medCount = 0;
  let lowCount = 0;
  let totalRiskScore = 0;

  for (const r of result.risks) {
    const lvl = getRiskLevel(r.top_score, highThreshold, mediumThreshold);
    if (lvl === 'HIGH') highCount++;
    else if (lvl === 'MEDIUM') medCount++;
    else lowCount++;
    totalRiskScore += r.top_score;
  }

  const avgRiskScore = result.risks.length > 0 ? totalRiskScore / result.risks.length : 0;

  const handleExportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(result, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `ContractLens_Analysis_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handlePrint = () => {
    window.print();
  };

  const handleCopySummary = () => {
    const summary = `ContractLens Analysis Report
Contract: ${fileName || 'Agreement'}
Overall Risk: ${overallRisk}
Total Clauses: ${result.clauses.length}
High Risk Clauses: ${highCount}
Contradictions: ${result.internal_contradictions.length}
Evaluated against: Indian Contract Act 1872, IPC 1860, Constitution of India`;

    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="results-grid">
      {/* Top Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <button className="btn btn-secondary" onClick={onReset} style={{ padding: '0.5rem 0.95rem' }}>
          <ArrowLeft size={16} />
          Analyse Another Agreement
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <button className="btn btn-secondary" onClick={handleCopySummary} style={{ padding: '0.5rem 0.95rem', fontSize: '0.82rem' }}>
            {copied ? <Check size={15} color="#166534" /> : <Share2 size={15} />}
            {copied ? 'Copied Summary!' : 'Copy Summary'}
          </button>

          <button className="btn btn-secondary" onClick={handlePrint} style={{ padding: '0.5rem 0.95rem', fontSize: '0.82rem' }}>
            <Printer size={15} />
            Print Report
          </button>

          <button className="btn btn-primary" onClick={handleExportJSON} style={{ padding: '0.5rem 0.95rem', fontSize: '0.82rem' }}>
            <Download size={15} />
            Export JSON
          </button>
        </div>
      </div>

      {/* 1. Risk Alert Banner */}
      <RiskBanner
        overallRisk={overallRisk}
        highCount={highCount}
        contradictionCount={result.internal_contradictions.length}
      />

      {/* 2. Key Performance Metrics */}
      <MetricCards
        totalClauses={result.clauses.length}
        highRiskCount={highCount}
        mediumRiskCount={medCount}
        contradictionCount={result.internal_contradictions.length}
        avgRiskScore={avgRiskScore}
      />

      {/* 3. Risk Distribution Meter */}
      <RiskMeter
        highCount={highCount}
        mediumCount={medCount}
        lowCount={lowCount}
        total={result.clauses.length}
      />

      {/* 4. Interactive 2D Knowledge Graph */}
      <KnowledgeGraph
        clauses={result.clauses}
        edges={result.graph_edges}
        risks={result.risks}
        contradictions={result.internal_contradictions}
        highThreshold={highThreshold}
        mediumThreshold={mediumThreshold}
        onSelectClause={(idx) => setSelectedClauseId(idx)}
      />

      {/* 5. Side-by-Side Contradictions */}
      <ContradictionCards
        contradictions={result.internal_contradictions}
        clauses={result.clauses}
      />

      {/* 6. Clause Risk Matrix */}
      <ClauseMatrix
        clauses={result.clauses}
        risks={result.risks}
        highThreshold={highThreshold}
        mediumThreshold={mediumThreshold}
        selectedClauseId={selectedClauseId}
      />

      {/* 7. Statutory Law Cross-References (Qdrant RAG) */}
      <LawMatches lawChecks={result.law_checks} />

      {/* 8. AI Legal Explanations */}
      <AIExplainer explanations={result.explanations} />
    </div>
  );
};
