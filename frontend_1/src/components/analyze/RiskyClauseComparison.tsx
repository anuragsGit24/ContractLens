import React, { useState } from 'react';
import {
  ShieldAlert,
  Copy,
  Check,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Info,
  Scale
} from 'lucide-react';
import type { Clause, ClauseExplanation, ClauseRisk } from '../../types/contract';
import { parseExplanation } from '../../utils/formatters';
import {
  computeClauseDiff,
  extractRewriteDetails,
  segmentTextBySpans,
  type HighlightSpan,
} from '../../utils/textHighlighting';

interface RiskyClauseComparisonProps {
  explanations: ClauseExplanation[];
  clauses: Clause[];
  risks: ClauseRisk[];
}

export const RiskyClauseComparison: React.FC<RiskyClauseComparisonProps> = ({
  explanations,
  clauses,
  risks,
}) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [expandedClauses, setExpandedClauses] = useState<Record<string, boolean>>({});

  const clauseMap = new Map<number, Clause>();
  for (const c of clauses) {
    clauseMap.set(c.index, c);
  }

  const riskMap = new Map<number, ClauseRisk>();
  for (const r of risks) {
    riskMap.set(r.clause_index, r);
  }

  const handleCopy = (text: string, clauseIndex: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(clauseIndex);
    setTimeout(() => {
      setCopiedIndex(null);
    }, 2500);
  };

  const toggleExpand = (key: string) => {
    setExpandedClauses((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const renderHighlightedOriginal = (
    originalText: string,
    spans: HighlightSpan[],
    uniqueKey: string
  ) => {
    if (!originalText) return <span>Content unavailable</span>;

    const isLong = originalText.length > 280;
    const isExpanded = expandedClauses[uniqueKey] ?? false;

    let textToDisplay = originalText;
    let activeSpans = spans;

    if (isLong && !isExpanded) {
      // Check if any highlight is beyond 260
      const hasLateHighlight = spans.some((s) => s.end > 250);
      if (!hasLateHighlight) {
        textToDisplay = originalText.slice(0, 250) + '...';
        activeSpans = spans
          .filter((s) => s.start < 250)
          .map((s) => ({ ...s, end: Math.min(s.end, 250) }));
      }
    }

    const segments = segmentTextBySpans(textToDisplay, activeSpans);

    return (
      <div>
        <p className="clause-text" style={{ lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
          {segments.map((seg, i) => {
            if (seg.isHighlighted) {
              return (
                <mark
                  key={i}
                  className="highlight-risky-wording"
                  title={seg.label || 'Risky wording identified'}
                >
                  {seg.text}
                </mark>
              );
            }
            return <span key={i}>{seg.text}</span>;
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
                View full clause ({originalText.length} chars)
              </>
            )}
          </button>
        )}
      </div>
    );
  };

  const renderHighlightedRewrite = (
    rewriteText: string,
    spans: HighlightSpan[],
    uniqueKey: string
  ) => {
    const isLong = rewriteText.length > 320;
    const isExpanded = expandedClauses[uniqueKey] ?? false;

    let textToDisplay = rewriteText;
    let activeSpans = spans;

    if (isLong && !isExpanded) {
      const hasLateHighlight = spans.some((s) => s.end > 300);
      if (!hasLateHighlight) {
        textToDisplay = rewriteText.slice(0, 300) + '...';
        activeSpans = spans
          .filter((s) => s.start < 300)
          .map((s) => ({ ...s, end: Math.min(s.end, 300) }));
      }
    }

    const segments = segmentTextBySpans(textToDisplay, activeSpans);

    return (
      <div>
        <p
          className="clause-text"
          style={{
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            color: 'var(--text-primary)',
            fontStyle: 'normal',
          }}
        >
          {segments.map((seg, i) => {
            if (seg.isHighlighted) {
              return (
                <mark
                  key={i}
                  className="highlight-safer-wording"
                  title={seg.label || 'Safer suggested wording'}
                >
                  {seg.text}
                </mark>
              );
            }
            return <span key={i}>{seg.text}</span>;
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
                View full rewrite ({rewriteText.length} chars)
              </>
            )}
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="card">
      {/* Section Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <div className="section-heading" style={{ marginBottom: '0.15rem' }}>
            Risky Clauses &amp; Safer Suggested Rewrites
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Comparative side-by-side analysis highlighting specific risky language, legal rationale, and proposed safer redlines
          </p>
        </div>

        <span className="pill pill-info">
          <Sparkles size={13} />
          {explanations.length} Clause{explanations.length === 1 ? '' : 's'} Evaluated
        </span>
      </div>

      {/* Legend */}
      <div className="contradiction-legend">
        <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Redline Legend:
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span className="legend-chip">
            <span className="legend-dot legend-dot-contradiction" />
            <strong>Risky wording</strong> (unilateral liability, missing caps, void terms)
          </span>
          <span className="legend-chip">
            <span className="legend-dot legend-dot-safe" />
            <strong>Safer wording</strong> (clarified bounds, cure periods, balanced standards)
          </span>
          <span className="legend-chip">
            <span className="legend-dot legend-dot-context" />
            <strong>Unchanged context</strong> (exact contract wording retained)
          </span>
        </div>
      </div>

      {explanations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
          No high-risk clauses required LLM explanation under current risk thresholds.
        </div>
      ) : (
        <div className="risky-comparison-container">
          {explanations.map((exp) => {
            const clause = clauseMap.get(exp.clause_index);
            const risk = riskMap.get(exp.clause_index);
            const parsed = parseExplanation(exp.explanation);
            const passed = exp.citation_verification ? exp.citation_verification.passed : true;

            const hasRewrite = Boolean(parsed.rewrite && parsed.rewrite.trim().length > 0);
            const rewriteDetails = extractRewriteDetails(parsed.rewrite);

            // Compute exact word-level diff between original clause and suggested rewrite
            const originalText = clause?.text || '';
            const rewriteText = rewriteDetails.clauseText || parsed.rewrite || '';

            const diffResult = hasRewrite
              ? computeClauseDiff(originalText, rewriteText)
              : { hasDiff: false, originalSpans: [], rewriteSpans: [], overlapRatio: 0 };

            // Determine original clause risky wording spans
            let effectiveOrigSpans = diffResult.originalSpans;
            let effectiveRewrSpans = diffResult.rewriteSpans;

            // If rewrite is advisory guidance (no in-place token diff), highlight the operative risky sentence cleanly
            if (!diffResult.hasDiff && originalText) {
              const operativeRegex = /\b(?:no\s+payment|shall\s+not|without\s+liability|unilateral\w*|sole\s+discretion|indemnif\w*|penalty|exorbitant|void|restrain\w*|except\s+with\s+the\s+prior|cost\s+estimates|breach\s+or\s+violation)\b/i;
              const match = originalText.match(operativeRegex);
              if (match && match.index !== undefined) {
                const prev = originalText.slice(0, match.index);
                const next = originalText.slice(match.index);
                const startSemi = prev.lastIndexOf('; ');
                const startDot = prev.lastIndexOf('. ');
                const startNewline = prev.lastIndexOf('\n');

                const start = Math.max(
                  startSemi !== -1 ? startSemi + 2 : 0,
                  startDot !== -1 ? startDot + 2 : 0,
                  startNewline !== -1 ? startNewline + 1 : 0,
                  0
                );

                const nextSemi = next.indexOf(';');
                const nextDot = next.indexOf('. ');
                const nextNewline = next.indexOf('\n');

                let relEnd = next.length;
                if (nextSemi !== -1 && nextSemi < relEnd) relEnd = nextSemi;
                if (nextDot !== -1 && nextDot < relEnd) relEnd = nextDot + 1;
                if (nextNewline !== -1 && nextNewline < relEnd) relEnd = nextNewline;

                const end = match.index + relEnd;

                effectiveOrigSpans = [{
                  start,
                  end,
                  type: 'risky',
                  label: 'Risky wording identified',
                }];
              }
              // For advisory text, don't splatter random green highlights on words
              effectiveRewrSpans = [];
            }

            // Determine why this rewrite reduces risk
            let whyReducesRisk = '';
            if (hasRewrite) {
              if (rewriteDetails.rationale && rewriteDetails.hasQuotedClause) {
                whyReducesRisk = rewriteDetails.rationale;
              } else if (parsed.whyRisky && parsed.whyRisky.length > 20) {
                whyReducesRisk = `Remedies the legal defect identified under Indian law: ${parsed.whyRisky.slice(0, 180)}...`;
              } else {
                whyReducesRisk = `Replaces broad, unilateral stipulations with objectively bounded, legally enforceable obligations.`;
              }
            }

            const riskLevel = risk?.risk_level ? risk.risk_level.toUpperCase() : 'HIGH';

            return (
              <div key={exp.clause_index} className="risky-clause-row-card">
                {/* Clause Meta Banner */}
                <div className="risky-row-meta-banner">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                      Clause {exp.clause_index}
                    </span>
                    {clause?.label && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        — {clause.label}
                      </span>
                    )}
                    {risk?.top_category && (
                      <span className="pill pill-neutral" style={{ textTransform: 'capitalize', fontSize: '0.74rem' }}>
                        {risk.top_category}
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {risk && (
                      <span className="pill pill-neutral" style={{ fontSize: '0.74rem' }}>
                        Risk Score: {risk.top_score.toFixed(3)}
                      </span>
                    )}
                    <span className={`pill pill-${riskLevel === 'HIGH' ? 'high' : riskLevel === 'MEDIUM' ? 'med' : 'low'}`} style={{ fontSize: '0.74rem' }}>
                      <ShieldAlert size={12} />
                      {riskLevel} RISK
                    </span>
                    {passed ? (
                      <span className="pill pill-low" style={{ fontSize: '0.72rem' }} title="Citations grounded in retrieved evidence">
                        <CheckCircle2 size={12} />
                        Citations Verified
                      </span>
                    ) : (
                      <span className="pill pill-med" style={{ fontSize: '0.72rem' }} title="External or unverified citation flagged">
                        <AlertTriangle size={12} />
                        Unverified Citations
                      </span>
                    )}
                  </div>
                </div>

                {/* Warning if LLM had timeout or error */}
                {exp.warning && (
                  <div style={{ margin: '0.85rem 1rem 0', padding: '0.5rem 0.75rem', background: '#FFF4DB', border: '1px solid #F9DFA7', color: '#92400E', borderRadius: 'var(--radius-sm)', fontSize: '0.78rem' }}>
                    ⚠ {exp.warning.includes('Read timed out')
                      ? 'Ollama generation exceeded time limit. Risk scoring and law matches are verified below.'
                      : exp.warning}
                  </div>
                )}

                {/* 3-Column Comparison Grid: Original Clause | Risk Identified | Safer Suggested Rewrite */}
                <div className="risky-comparison-grid">
                  {/* Column 1: Original Clause with Risky Wording Highlighted */}
                  <div className="comparison-col comparison-col-original">
                    <div className="comparison-col-header">
                      <div className="comparison-col-title">
                        <span>Original Clause</span>
                        <span className="badge-highlight-indicator" style={{ background: 'var(--risk-high-bg)', color: 'var(--risk-high-text)', borderColor: 'var(--risk-high-border)' }}>
                          Risky wording
                        </span>
                      </div>
                      <div className="comparison-col-desc">
                        Exact contract wording preserved verbatim
                      </div>
                    </div>

                    <div className="comparison-col-body">
                      {renderHighlightedOriginal(
                        originalText,
                        effectiveOrigSpans,
                        `orig_${exp.clause_index}`
                      )}
                    </div>
                  </div>

                  {/* Column 2: Risk Identified & Rationale */}
                  <div className="comparison-col comparison-col-risk">
                    <div className="comparison-col-header">
                      <div className="comparison-col-title">
                        <span>Risk Identified</span>
                        <span className="badge-highlight-indicator" style={{ background: '#EFF6FF', color: '#1E40AF', borderColor: '#BFDBFE' }}>
                          Legal Analysis
                        </span>
                      </div>
                      <div className="comparison-col-desc">
                        Plain-language legal &amp; commercial risk assessment
                      </div>
                    </div>

                    <div className="comparison-col-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {/* Risk Summary */}
                      {parsed.riskSummary && (
                        <div>
                          <div className="explainer-section-subhead">Risk Summary</div>
                          <p className="explainer-text" style={{ fontSize: '0.81rem' }}>
                            {parsed.riskSummary}
                          </p>
                        </div>
                      )}

                      {/* Why Risky under Indian Law */}
                      {parsed.whyRisky && (
                        <div>
                          <div className="explainer-section-subhead">Statutory &amp; Legal Exposure</div>
                          <p className="explainer-text" style={{ fontSize: '0.81rem' }}>
                            {parsed.whyRisky}
                          </p>
                        </div>
                      )}

                      {/* Practical Impact */}
                      {parsed.practicalImpact && (
                        <div>
                          <div className="explainer-section-subhead">Practical Commercial Impact</div>
                          <p className="explainer-text" style={{ fontSize: '0.81rem' }}>
                            {parsed.practicalImpact}
                          </p>
                        </div>
                      )}

                      {/* Why Proposed Wording Reduces Risk */}
                      {hasRewrite && whyReducesRisk && (
                        <div className="why-reduces-risk-box">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.25rem' }}>
                            <Scale size={13} color="var(--risk-low-text)" />
                            <strong style={{ fontSize: '0.76rem', color: 'var(--risk-low-text)' }}>
                              Why this rewrite reduces risk:
                            </strong>
                          </div>
                          <p style={{ fontSize: '0.78rem', color: '#14532D', lineHeight: 1.5 }}>
                            {whyReducesRisk}
                          </p>
                        </div>
                      )}

                      {/* Grounded Citations */}
                      {parsed.citations && (
                        <div style={{ marginTop: '0.25rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-color)' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                            Grounded Citations:
                          </span>
                          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.74rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                            {parsed.citations}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Column 3: Safer Suggested Rewrite with Changes Highlighted */}
                  <div className="comparison-col comparison-col-rewrite">
                    <div className="comparison-col-header">
                      <div className="comparison-col-title">
                        <span>Safer Suggested Rewrite</span>
                        {hasRewrite && (
                          <span className="badge-highlight-indicator" style={{ background: '#ECFDF5', color: '#065F46', borderColor: '#A7F3D0' }}>
                            {rewriteDetails.isAdvisory ? 'Drafting Revision' : 'Suggested rewrite'}
                          </span>
                        )}
                      </div>
                      <div className="comparison-col-desc">
                        {rewriteDetails.isAdvisory ? 'Actionable drafting revision to mitigate legal exposure' : 'Proposed replacement with changes emphasized'}
                      </div>
                    </div>

                    <div className="comparison-col-body">
                      {hasRewrite ? (
                        <>
                          <div className="rewrite-content-box">
                            {renderHighlightedRewrite(
                              rewriteText,
                              effectiveRewrSpans,
                              `rewr_${exp.clause_index}`
                            )}
                          </div>

                          {/* Copy Button & Action Toolbar */}
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <button
                              type="button"
                              className="btn btn-secondary copy-rewrite-btn"
                              onClick={() => handleCopy(rewriteText, exp.clause_index)}
                              title="Copy suggested rewrite to clipboard"
                            >
                              {copiedIndex === exp.clause_index ? (
                                <>
                                  <Check size={14} color="#166534" />
                                  <span>Copied Rewrite!</span>
                                </>
                              ) : (
                                <>
                                  <Copy size={14} />
                                  <span>Copy Rewrite</span>
                                </>
                              )}
                            </button>

                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                              Model: {exp.model_name || 'Ollama'}
                            </span>
                          </div>

                          {/* Mandatory Legal Review Disclaimer */}
                          <div className="legal-disclaimer-box">
                            <Info size={13} style={{ flexShrink: 0, marginTop: '2px' }} />
                            <span>
                              <strong>Legal Disclaimer:</strong> AI-generated drafting suggestion. For internal review only — requires review and formal approval by qualified legal counsel.
                            </span>
                          </div>
                        </>
                      ) : (
                        /* Empty state when LLM has not generated a rewrite */
                        <div className="rewrite-empty-state">
                          <AlertTriangle size={24} color="var(--risk-med-solid)" style={{ marginBottom: '0.5rem' }} />
                          <h5 style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                            No Automated Rewrite Generated
                          </h5>
                          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                            The LLM analysis did not supply an alternative drafting proposal for this clause under current risk parameters.
                          </p>
                          <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', background: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.74rem', color: 'var(--text-secondary)' }}>
                            <strong>Recommendation:</strong> Use the Risk Identified column and statutory cross-references to draft manual adjustments.
                          </div>
                        </div>
                      )}
                    </div>
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
