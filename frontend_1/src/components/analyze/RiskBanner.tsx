import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2 } from 'lucide-react';

interface RiskBannerProps {
  overallRisk: 'HIGH' | 'MEDIUM' | 'LOW';
  highCount: number;
  contradictionCount: number;
}

export const RiskBanner: React.FC<RiskBannerProps> = ({
  overallRisk,
  highCount,
  contradictionCount,
}) => {
  if (overallRisk === 'HIGH') {
    return (
      <div className="risk-banner risk-banner-high">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <AlertTriangle size={24} />
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.98rem' }}>High Risk Contract Profile Detected</div>
            <div style={{ fontSize: '0.82rem', opacity: 0.9 }}>
              {highCount} high-risk clause{highCount === 1 ? '' : 's'} and {contradictionCount} drafting contradiction{contradictionCount === 1 ? '' : 's'} require immediate legal renegotiation.
            </div>
          </div>
        </div>
        <span className="pill pill-high" style={{ fontWeight: 800, fontSize: '0.82rem' }}>HIGH RISK</span>
      </div>
    );
  }

  if (overallRisk === 'MEDIUM') {
    return (
      <div className="risk-banner risk-banner-med">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <AlertCircle size={24} />
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.98rem' }}>Moderate Commercial &amp; Legal Risk Detected</div>
            <div style={{ fontSize: '0.82rem', opacity: 0.9 }}>
              Validate obligations, indemnity caps, and termination notice periods before final execution.
            </div>
          </div>
        </div>
        <span className="pill pill-med" style={{ fontWeight: 800, fontSize: '0.82rem' }}>MEDIUM RISK</span>
      </div>
    );
  }

  return (
    <div className="risk-banner risk-banner-low">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <CheckCircle2 size={24} />
        <div>
          <div style={{ fontWeight: 800, fontSize: '0.98rem' }}>Low Risk Contract Profile</div>
          <div style={{ fontSize: '0.82rem', opacity: 0.9 }}>
            No critical statutory breaches or severe liability limitations were identified.
          </div>
        </div>
      </div>
      <span className="pill pill-low" style={{ fontWeight: 800, fontSize: '0.82rem' }}>LOW RISK</span>
    </div>
  );
};
