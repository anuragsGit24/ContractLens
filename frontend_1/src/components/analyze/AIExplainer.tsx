import React, { useState } from 'react';
import { Sparkles, AlertTriangle, CheckCircle2, Columns3, LayoutList } from 'lucide-react';
import type { Clause, ClauseExplanation, ClauseRisk } from '../../types/contract';
import { parseExplanation } from '../../utils/formatters';
import { RiskyClauseComparison } from './RiskyClauseComparison';

interface AIExplainerProps {
  explanations: ClauseExplanation[];
  clauses?: Clause[];
  risks?: ClauseRisk[];
}

export const AIExplainer: React.FC<AIExplainerProps> = ({
  explanations,
  clauses = [],
  risks = [],
}) => {
  const [viewMode, setViewMode] = useState<'comparison' | 'cards'>('comparison');

  return (
    <div>
      {/* View Switcher Toolbar */}
      {clauses.length > 0 && explanations.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.65rem' }}>
          <div className="filter-btn-group" style={{ display: 'inline-flex' }}>
            <button
              type="button"
              className={`filter-btn ${viewMode === 'comparison' ? 'active' : ''}`}
              onClick={() => setViewMode('comparison')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.76rem', padding: '0.3rem 0.65rem' }}
              title="Side-by-side comparative table: Original | Risk | Safer Rewrite"
            >
              <Columns3 size={13} />
              Comparison Table
            </button>
            <button
              type="button"
              className={`filter-btn ${viewMode === 'cards' ? 'active' : ''}`}
              onClick={() => setViewMode('cards')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.76rem', padding: '0.3rem 0.65rem' }}
              title="Detailed audit card view"
            >
              <LayoutList size={13} />
              Audit Cards
            </button>
          </div>
        </div>
      )}

      {viewMode === 'comparison' && clauses.length > 0 ? (
        <RiskyClauseComparison
          explanations={explanations}
          clauses={clauses}
          risks={risks}
        />
      ) : (
        /* Classic Audit Cards View */
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
            <div>
              <div className="section-heading" style={{ marginBottom: '0.15rem' }}>
                AI Legal Risk Advisory &amp; Verified Explanations
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Plain-English risk rationale, business implications, and actionable drafting suggestions generated via Ollama
              </p>
            </div>

            <span className="pill pill-info">
              <Sparkles size={13} />
              {explanations.length} Explanation{explanations.length === 1 ? '' : 's'} Generated
            </span>
          </div>

          {explanations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
              No high-risk clauses required LLM explanation under current risk thresholds.
            </div>
          ) : (
            explanations.map((item) => {
              const parsed = parseExplanation(item.explanation);
              const passed = item.citation_verification ? item.citation_verification.passed : true;

              return (
                <div key={item.clause_index} className="ai-explainer-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <h4 className="explainer-title">
                      Clause {item.clause_index} Legal Analysis
                    </h4>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {passed ? (
                        <span className="pill pill-low" title="All citations verified against Qdrant evidence">
                          <CheckCircle2 size={13} />
                          Citations Verified
                        </span>
                      ) : (
                        <span className="pill pill-med" title="Some cited provisions are external or unverified">
                          <AlertTriangle size={13} />
                          Unverified Citations Flagged
                        </span>
                      )}

                      <span className="pill pill-neutral" style={{ fontSize: '0.74rem' }}>
                        Model: {item.model_name || 'Ollama'}
                      </span>
                    </div>
                  </div>

                  {item.warning && (
                    <div style={{ marginBottom: '0.75rem', padding: '0.5rem 0.75rem', background: '#FFF4DB', border: '1px solid #F9DFA7', color: '#92400E', borderRadius: 'var(--radius-sm)', fontSize: '0.78rem' }}>
                      ⚠ {item.warning.includes('Read timed out')
                        ? 'Ollama generation exceeded time limit. Risk scoring and retrieved law matches are still available.'
                        : item.warning}
                    </div>
                  )}

                  {/* 1. Risk Summary */}
                  {parsed.riskSummary && (
                    <div>
                      <div className="explainer-section-title">1. Risk Summary</div>
                      <p className="explainer-text">{parsed.riskSummary}</p>
                    </div>
                  )}

                  {/* 2. Why Risky */}
                  {parsed.whyRisky && (
                    <div>
                      <div className="explainer-section-title">2. Why Risky Under Indian Law</div>
                      <p className="explainer-text">{parsed.whyRisky}</p>
                    </div>
                  )}

                  {/* 3. Practical Impact */}
                  {parsed.practicalImpact && (
                    <div>
                      <div className="explainer-section-title">3. Practical Impact on Business</div>
                      <p className="explainer-text">{parsed.practicalImpact}</p>
                    </div>
                  )}

                  {/* 4. Safer Rewrite */}
                  {parsed.rewrite && (
                    <div>
                      <div className="explainer-section-title">4. Safer Rewrite Suggestion</div>
                      <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', fontSize: '0.84rem', color: '#1E293B', fontStyle: 'italic' }}>
                        "{parsed.rewrite}"
                      </div>
                    </div>
                  )}

                  {/* 5. Citations */}
                  {parsed.citations && (
                    <div>
                      <div className="explainer-section-title">5. Grounded Citations</div>
                      <p className="explainer-text" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                        {parsed.citations}
                      </p>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};
