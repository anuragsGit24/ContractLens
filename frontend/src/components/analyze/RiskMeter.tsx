import React from 'react';

interface RiskMeterProps {
  highCount: number;
  mediumCount: number;
  lowCount: number;
  total: number;
}

export const RiskMeter: React.FC<RiskMeterProps> = ({
  highCount,
  mediumCount,
  lowCount,
  total,
}) => {
  const safeTotal = total > 0 ? total : 1;
  const highPct = ((highCount / safeTotal) * 100).toFixed(1);
  const medPct = ((mediumCount / safeTotal) * 100).toFixed(1);
  const lowPct = ((lowCount / safeTotal) * 100).toFixed(1);

  return (
    <div className="risk-meter-wrap">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)' }}>
          Risk Distribution Breakdown
        </span>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          {total} Total Clauses Evaluated
        </span>
      </div>

      <div className="risk-meter-track">
        <div className="meter-seg-high" style={{ width: `${highPct}%` }} title={`High Risk: ${highCount} (${highPct}%)`} />
        <div className="meter-seg-med" style={{ width: `${medPct}%` }} title={`Medium Risk: ${mediumCount} (${medPct}%)`} />
        <div className="meter-seg-low" style={{ width: `${lowPct}%` }} title={`Low Risk: ${lowCount} (${lowPct}%)`} />
      </div>

      <div className="risk-meter-legend">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span className="legend-dot" style={{ backgroundColor: 'var(--risk-high-solid)' }} />
          <span>High Risk: <strong>{highCount}</strong> ({highPct}%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span className="legend-dot" style={{ backgroundColor: 'var(--risk-med-solid)' }} />
          <span>Medium Risk: <strong>{mediumCount}</strong> ({medPct}%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span className="legend-dot" style={{ backgroundColor: 'var(--risk-low-solid)' }} />
          <span>Low Risk: <strong>{lowCount}</strong> ({lowPct}%)</span>
        </div>
      </div>
    </div>
  );
};
