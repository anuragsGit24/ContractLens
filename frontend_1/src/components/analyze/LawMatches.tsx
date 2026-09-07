import React from 'react';
import { BookMarked } from 'lucide-react';
import type { ClauseLawCheck } from '../../types/contract';
import { getActShortName } from '../../utils/formatters';

interface LawMatchesProps {
  lawChecks: ClauseLawCheck[];
}

export const LawMatches: React.FC<LawMatchesProps> = ({ lawChecks }) => {
  // Aggregate all matches across clauses
  const activeChecks = lawChecks.filter((c) => c.law_matches && c.law_matches.length > 0);

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
        <div>
          <div className="section-heading" style={{ marginBottom: '0.15rem' }}>
            Statutory Law Cross-References (Qdrant RAG)
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Indian statutes retrieved and cross-referenced against contract clauses
          </p>
        </div>

        <span className="pill pill-info">
          <BookMarked size={13} />
          {activeChecks.length} Clause{activeChecks.length === 1 ? '' : 's'} Matched
        </span>
      </div>

      {activeChecks.length === 0 ? (
        <div style={{ padding: '1.5rem', background: 'var(--bg-app)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', color: 'var(--text-muted)', textAlign: 'center', fontSize: '0.86rem' }}>
          No statutory conflicts or high-similarity law matches flagged for manual review.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {activeChecks.map((check) => (
            <div key={check.clause_index} style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '0.85rem 1rem', background: '#FAFAFA' }}>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Clause {check.clause_index} Statutory References
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {check.law_matches.map((m, idx) => {
                  const actShort = getActShortName(m.act);

                  return (
                    <div key={idx} style={{ background: '#FFFFFF', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '0.65rem 0.85rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                          <span className="pill pill-info" style={{ fontWeight: 700 }}>
                            {actShort} Sec {m.section_number}
                          </span>
                          <span style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-primary)' }}>
                            {m.title}
                          </span>
                        </div>

                        <span className="pill pill-neutral" style={{ fontSize: '0.74rem' }}>
                          Relevance: {(m.rerank_score * 100).toFixed(1)}%
                        </span>
                      </div>

                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                        {m.description.length > 220 ? `${m.description.slice(0, 220)}...` : m.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
