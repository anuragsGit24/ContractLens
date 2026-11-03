import React, { useState } from 'react';
import { GitCommit, CheckCircle2, AlertTriangle, ChevronDown, ChevronUp, Scale, Info } from 'lucide-react';
import type { Clause, InternalContradiction, ClauseExplanation } from '../../types/contract';
import { analyzeContradiction } from '../../utils/contradictionMatcher';
import { segmentTextBySpans, type HighlightSpan } from '../../utils/textHighlighting';

interface ContradictionCardsProps {
  contradictions: InternalContradiction[];
  clauses: Clause[];
  explanations?: ClauseExplanation[];
}

export const ContradictionCards: React.FC<ContradictionCardsProps> = ({
  contradictions,
  clauses,
  explanations,
}) => {
  const [expandedClauses, setExpandedClauses] = useState<Record<string, boolean>>({});

  const clauseMap = new Map<number, Clause>();
  for (const c of clauses) {
    clauseMap.set(c.index, c);
  }

  const toggleExpand = (key: string) => {
    setExpandedClauses((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const renderClauseContent = (
    clause: Clause | undefined,
    clauseIndex: number,
    spans: HighlightSpan[],
    uniqueKey: string
  ) => {
    if (!clause) {
      return (
        <p className="clause-text" style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
          Clause {clauseIndex} content unavailable in source document.
        </p>
      );
    }

    const text = clause.text || '';
    const isLong = text.length > 280;
    const isExpanded = expandedClauses[uniqueKey] ?? false;

    // Check if any highlight exists beyond character 280
    const hasLateHighlight = spans.some((s) => s.end > 260);

    // If collapsed and long, truncate unless highlight is near the end
    let displayText = text;
    let effectiveSpans = spans;

    if (isLong && !isExpanded) {
      if (!hasLateHighlight) {
        displayText = text.slice(0, 260) + '...';
        effectiveSpans = spans.filter((s) => s.start < 260).map((s) => ({
          ...s,
          end: Math.min(s.end, 260),
        }));
      }
      // If highlight is later in the text, we show full or up to highlight so evidence is never hidden
    }

    const segments = segmentTextBySpans(displayText, effectiveSpans);

    return (
      <div>
        <p className="clause-text" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
          {segments.map((seg, idx) => {
            if (seg.isHighlighted) {
              const highlightClass =
                seg.type === 'tension'
                  ? 'highlight-contradiction-tension'
                  : 'highlight-contradiction';

              return (
                <mark
                  key={idx}
                  className={highlightClass}
                  title={seg.label || 'Conflicting passage'}
                >
                  {seg.text}
                </mark>
              );
            }
            return <span key={idx}>{seg.text}</span>;
          })}
        </p>

        {isLong && (
          <button
            type="button"
            className="btn btn-secondary clause-expand-btn"
            onClick={() => toggleExpand(uniqueKey)}
            style={{
              marginTop: '0.65rem',
              padding: '0.2rem 0.55rem',
              fontSize: '0.74rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.3rem',
            }}
          >
            {isExpanded ? (
              <>
                <ChevronUp size={13} />
                Show less
              </>
            ) : (
              <>
                <ChevronDown size={13} />
                View full clause ({text.length} chars)
              </>
            )}
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="card">
      {/* Header and Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <div className="section-heading" style={{ marginBottom: '0.15rem' }}>
            Intra-Contract Drafting Contradictions
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Directly highlighted conflicting terms, incompatible deadlines, and opposing legal obligations
          </p>
        </div>

        <span className="pill pill-med">
          <GitCommit size={13} />
          {contradictions.length} Conflict{contradictions.length === 1 ? '' : 's'} Flagged
        </span>
      </div>

      {/* Contradiction Highlighting Legend */}
      <div className="contradiction-legend">
        <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Highlight Guide:
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span className="legend-chip">
            <span className="legend-dot legend-dot-contradiction" />
            <strong>Conflicting passage</strong> (direct tension or opposing terms)
          </span>
          <span className="legend-chip">
            <span className="legend-dot legend-dot-context" />
            <strong>Surrounding context</strong> (preserved verbatim)
          </span>
          <span className="legend-chip">
            <span className="legend-dot legend-dot-info" />
            <strong>Confidence score</strong> (graph similarity + polarity check)
          </span>
        </div>
      </div>

      {contradictions.length === 0 ? (
        <div
          style={{
            padding: '1.5rem',
            background: '#F0FDF4',
            border: '1px solid #BBF7D0',
            borderRadius: 'var(--radius-md)',
            color: '#166534',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            fontSize: '0.88rem',
          }}
        >
          <CheckCircle2 size={20} color="#166534" />
          <span>No internal drafting contradictions detected across clauses. All obligations appear harmonious.</span>
        </div>
      ) : (
        <div className="contradictions-list">
          {contradictions.map((item, idx) => {
            const clauseA = clauseMap.get(item.clause_a_index);
            const clauseB = clauseMap.get(item.clause_b_index);

            // Run deterministic contradiction analysis and span identification
            const analysis = analyzeContradiction(
              clauseA || { index: item.clause_a_index, label: `Clause ${item.clause_a_index}`, text: '' },
              clauseB || { index: item.clause_b_index, label: `Clause ${item.clause_b_index}`, text: '' },
              item.contradiction_score,
              explanations
            );

            const confidencePercent = (item.contradiction_score * 100).toFixed(0);

            return (
              <div key={idx} className="contradiction-card">
                {/* Pair Header Meta */}
                <div className="contradiction-pair-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                    <span className="pill pill-high" style={{ fontWeight: 700, fontSize: '0.76rem' }}>
                      <AlertTriangle size={12} />
                      Conflict #{idx + 1}
                    </span>
                    <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Clause {item.clause_a_index} vs Clause {item.clause_b_index}
                    </span>
                    <span className="pill pill-neutral" style={{ textTransform: 'capitalize', fontSize: '0.72rem' }}>
                      Topic: {analysis.topic}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {analysis.hasExactSpans ? (
                      <span className="pill pill-high" style={{ fontSize: '0.72rem' }}>
                        Passage Pinpointed
                      </span>
                    ) : (
                      <span className="pill pill-med" style={{ fontSize: '0.72rem' }}>
                        Full Clause Tension
                      </span>
                    )}
                    <span className="pill pill-neutral" style={{ fontSize: '0.72rem', fontWeight: 700 }}>
                      Score: {confidencePercent}%
                    </span>
                  </div>
                </div>

                {/* Side-by-Side Clause Comparison Grid */}
                <div className="contradiction-grid">
                  {/* Clause A Box */}
                  <div className="clause-box contradiction-clause-box">
                    <div className="clause-box-header">
                      <div>
                        <div className="clause-header">Clause {item.clause_a_index}</div>
                        {clauseA?.label && (
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            {clauseA.label}
                          </div>
                        )}
                      </div>

                      {analysis.hasExactSpans && analysis.spansA.length > 0 && (
                        <span className="badge-highlight-indicator">
                          Conflicting passage
                        </span>
                      )}
                    </div>

                    {renderClauseContent(clauseA, item.clause_a_index, analysis.spansA, `c_${idx}_a`)}
                  </div>

                  {/* Central VS Divider */}
                  <div className="vs-divider-container">
                    <div className="vs-badge">VS</div>
                    <div className="vs-confidence-tag">
                      {confidencePercent}% Conf
                    </div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-subtle)', marginTop: '0.2rem', textAlign: 'center' }}>
                      {item.relation || 'Conflict'}
                    </div>
                  </div>

                  {/* Clause B Box */}
                  <div className="clause-box contradiction-clause-box">
                    <div className="clause-box-header">
                      <div>
                        <div className="clause-header">Clause {item.clause_b_index}</div>
                        {clauseB?.label && (
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            {clauseB.label}
                          </div>
                        )}
                      </div>

                      {analysis.hasExactSpans && analysis.spansB.length > 0 && (
                        <span className="badge-highlight-indicator">
                          Conflicting passage
                        </span>
                      )}
                    </div>

                    {renderClauseContent(clauseB, item.clause_b_index, analysis.spansB, `c_${idx}_b`)}
                  </div>
                </div>

                {/* Contradiction Explanation Callout Box */}
                <div className="contradiction-explanation-box">
                  <div className="contradiction-explanation-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                      <Scale size={16} color="var(--risk-high-text)" />
                      <strong style={{ fontSize: '0.84rem', color: 'var(--risk-high-text)' }}>
                        Why these clauses conflict:
                      </strong>
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--risk-high-text)', fontWeight: 600 }}>
                      Category: {analysis.topic}
                    </span>
                  </div>

                  <p className="contradiction-explanation-text">
                    {analysis.explanation}
                  </p>

                  <div className="contradiction-remedy-note">
                    <Info size={13} style={{ flexShrink: 0, marginTop: '2px' }} />
                    <span>
                      <strong>Drafting Action:</strong> {analysis.remedySuggestion}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
