import React from 'react';
import { GitCommit, CheckCircle2 } from 'lucide-react';
import type { Clause, InternalContradiction } from '../../types/contract';

interface ContradictionCardsProps {
  contradictions: InternalContradiction[];
  clauses: Clause[];
}

export const ContradictionCards: React.FC<ContradictionCardsProps> = ({
  contradictions,
  clauses,
}) => {
  const clauseMap = new Map<number, Clause>();
  for (const c of clauses) {
    clauseMap.set(c.index, c);
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
        <div>
          <div className="section-heading" style={{ marginBottom: '0.15rem' }}>
            Intra-Contract Drafting Contradictions
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Detected opposing obligations, conflicting liabilities, or mutual exclusions within this agreement
          </p>
        </div>

        <span className="pill pill-med">
          <GitCommit size={13} />
          {contradictions.length} Conflict{contradictions.length === 1 ? '' : 's'} Flagged
        </span>
      </div>

      {contradictions.length === 0 ? (
        <div style={{ padding: '1.5rem', background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: 'var(--radius-md)', color: '#166534', display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.88rem' }}>
          <CheckCircle2 size={20} color="#166534" />
          <span>No internal drafting contradictions detected across clauses.</span>
        </div>
      ) : (
        <div className="contradictions-list">
          {contradictions.map((item, idx) => {
            const clauseA = clauseMap.get(item.clause_a_index);
            const clauseB = clauseMap.get(item.clause_b_index);

            return (
              <div key={idx} className="contradiction-card">
                <div className="contradiction-grid">
                  {/* Clause A */}
                  <div className="clause-box">
                    <div className="clause-header">Clause {item.clause_a_index}</div>
                    <p className="clause-text">
                      {clauseA ? clauseA.text : `Clause ${item.clause_a_index} content unavailable`}
                    </p>
                  </div>

                  {/* VS Divider */}
                  <div style={{ textAlign: 'center' }}>
                    <div className="vs-badge">VS</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.35rem', fontWeight: 600 }}>
                      Conf: {(item.contradiction_score * 100).toFixed(0)}%
                    </div>
                  </div>

                  {/* Clause B */}
                  <div className="clause-box">
                    <div className="clause-header">Clause {item.clause_b_index}</div>
                    <p className="clause-text">
                      {clauseB ? clauseB.text : `Clause ${item.clause_b_index} content unavailable`}
                    </p>
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
