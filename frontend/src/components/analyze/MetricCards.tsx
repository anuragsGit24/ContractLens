import React from 'react';
import { Layers, AlertTriangle, GitCommit, Target } from 'lucide-react';

interface MetricCardsProps {
  totalClauses: number;
  highRiskCount: number;
  mediumRiskCount: number;
  contradictionCount: number;
  avgRiskScore: number;
}

export const MetricCards: React.FC<MetricCardsProps> = ({
  totalClauses,
  highRiskCount,
  contradictionCount,
  avgRiskScore,
}) => {
  return (
    <div className="kpi-grid">
      <div className="kpi-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-label">Total Clauses</span>
          <Layers size={16} color="var(--accent)" />
        </div>
        <div className="kpi-val-row">
          <span className="kpi-value">{totalClauses}</span>
        </div>
        <div className="kpi-desc">Extracted &amp; normalized</div>
      </div>

      <div className="kpi-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-label">High Risk Clauses</span>
          <AlertTriangle size={16} color="#DC2626" />
        </div>
        <div className="kpi-val-row">
          <span className="kpi-value" style={{ color: highRiskCount > 0 ? '#DC2626' : 'var(--text-primary)' }}>
            {highRiskCount}
          </span>
        </div>
        <div className="kpi-desc">Score &ge; threshold</div>
      </div>

      <div className="kpi-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-label">Contradictions</span>
          <GitCommit size={16} color="#D97706" />
        </div>
        <div className="kpi-val-row">
          <span className="kpi-value" style={{ color: contradictionCount > 0 ? '#D97706' : 'var(--text-primary)' }}>
            {contradictionCount}
          </span>
        </div>
        <div className="kpi-desc">Intra-document conflicts</div>
      </div>

      <div className="kpi-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-label">Average Risk</span>
          <Target size={16} color="var(--accent)" />
        </div>
        <div className="kpi-val-row">
          <span className="kpi-value">{(avgRiskScore * 100).toFixed(1)}%</span>
        </div>
        <div className="kpi-desc">Cosine risk vector mean</div>
      </div>
    </div>
  );
};
