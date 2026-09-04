import React, { useState } from 'react';
import { Search, ChevronDown, ChevronUp, AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { Clause, ClauseRisk } from '../../types/contract';
import { getRiskLevel } from '../../utils/formatters';

interface ClauseMatrixProps {
  clauses: Clause[];
  risks: ClauseRisk[];
  highThreshold: number;
  mediumThreshold: number;
  selectedClauseId?: number | null;
}

export const ClauseMatrix: React.FC<ClauseMatrixProps> = ({
  clauses,
  risks,
  highThreshold,
  mediumThreshold,
  selectedClauseId,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  const riskMap = new Map<number, ClauseRisk>();
  for (const r of risks) {
    riskMap.set(r.clause_index, r);
  }

  const toggleExpand = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filteredClauses = clauses.filter((c) => {
    const risk = riskMap.get(c.index);
    const score = risk ? risk.top_score : 0;
    const level = getRiskLevel(score, highThreshold, mediumThreshold);

    if (filterLevel !== 'ALL' && level !== filterLevel) {
      return false;
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchText = c.text.toLowerCase().includes(query);
      const matchLabel = c.label.toLowerCase().includes(query);
      const matchCategory = (risk?.top_category || '').toLowerCase().includes(query);
      return matchText || matchLabel || matchCategory;
    }

    return true;
  });

  return (
    <div className="matrix-container">
      <div className="matrix-toolbar">
        <div>
          <div className="section-heading" style={{ marginBottom: '0.15rem' }}>
            Clause Risk Matrix
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Filterable breakdown of all extracted contract clauses and category scores
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          {/* Search bar */}
          <div style={{ position: 'relative', minWidth: '220px' }}>
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search clause text, keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
              style={{ paddingLeft: '2rem' }}
            />
          </div>

          {/* Filter button group */}
          <div className="filter-btn-group">
            {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((lvl) => (
              <button
                key={lvl}
                className={`filter-btn ${filterLevel === lvl ? 'active' : ''}`}
                onClick={() => setFilterLevel(lvl)}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Clause Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        {filteredClauses.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            No clauses match the active search and filter criteria.
          </div>
        ) : (
          filteredClauses.map((clause) => {
            const risk = riskMap.get(clause.index);
            const score = risk ? risk.top_score : 0;
            const level = getRiskLevel(score, highThreshold, mediumThreshold);
            const isExpanded = expandedIds.has(clause.index);
            const isSelected = selectedClauseId === clause.index;

            return (
              <div
                key={clause.index}
                className="clause-card"
                style={{
                  borderLeft: isSelected ? '4px solid var(--accent)' : undefined,
                  backgroundColor: isSelected ? '#F5F7FF' : undefined,
                }}
              >
                <div className="clause-card-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                      Clause {clause.index}
                    </span>

                    {risk?.top_category && (
                      <span className="pill pill-neutral" style={{ textTransform: 'capitalize' }}>
                        {risk.top_category}
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="pill pill-neutral">Score: {score.toFixed(3)}</span>
                    <span className={`pill pill-${level === 'HIGH' ? 'high' : level === 'MEDIUM' ? 'med' : 'low'}`}>
                      {level === 'HIGH' ? <AlertTriangle size={12} /> : <CheckCircle2 size={12} />}
                      {level}
                    </span>

                    <button
                      className="btn btn-secondary"
                      onClick={() => toggleExpand(clause.index)}
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                      title={isExpanded ? 'Collapse text' : 'Expand full text'}
                    >
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </div>
                </div>

                {/* Clause Snippet / Full Text */}
                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {isExpanded ? clause.text : clause.text.length > 220 ? `${clause.text.slice(0, 220)}...` : clause.text}
                </p>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
