import React from 'react';
import { 
  FileSearch, 
  AlertTriangle, 
  BookMarked, 
  ArrowRight, 
  Clock, 
  CheckCircle2, 
  FileText,
  Trash2
} from 'lucide-react';
import type { AnalysisHistoryItem, AnalyzeContractResponse } from '../../types/contract';

interface DashboardPageProps {
  history: AnalysisHistoryItem[];
  onSelectContract: (result: AnalyzeContractResponse) => void;
  onNewAnalysis: () => void;
  onClearHistory: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  history,
  onSelectContract,
  onNewAnalysis,
  onClearHistory,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Welcome Banner */}
      <div className="card" style={{ background: 'linear-gradient(135deg, #EEF2FF 0%, #FFFFFF 100%)', border: '1px solid #C7D2FE', padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <span className="pill pill-info" style={{ marginBottom: '0.65rem' }}>
              ⚡ AI-Powered Indian Contract Analysis
            </span>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
              Welcome to ContractLens Legal Intelligence
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '640px' }}>
              Screen your contracts for dangerous liability caps, non-compete overreaches, conflicting clauses, and statutory violations against the Indian Contract Act, IPC, and Constitution in under 20 seconds.
            </p>
          </div>
          <button className="btn btn-primary" onClick={onNewAnalysis} style={{ padding: '0.75rem 1.4rem' }}>
            <FileSearch size={18} />
            Analyse New Contract
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Feature Highlights */}
      <div>
        <div className="section-heading">Core Capabilities</div>
        <div className="steps-grid" style={{ maxWidth: '100%' }}>
          <div className="card">
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: '#FEE2E2', color: '#DC2626', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.85rem' }}>
              <AlertTriangle size={22} />
            </div>
            <h3 style={{ fontSize: '0.98rem', fontWeight: 700, marginBottom: '0.35rem' }}>Clause Risk Classification</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Zero-shot projection against 8 core Indian legal risk categories (unfair liability caps, unilateral termination, penalty clauses exceeding actual loss).
            </p>
          </div>

          <div className="card">
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: '#FEF3C7', color: '#D97706', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.85rem' }}>
              <FileSearch size={22} />
            </div>
            <h3 style={{ fontSize: '0.98rem', fontWeight: 700, marginBottom: '0.35rem' }}>Intra-Contract Contradictions</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Identifies opposing drafting obligations and mutual exclusions within the same document using high-speed polarity matching.
            </p>
          </div>

          <div className="card">
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: '#E0E7FF', color: '#4F46E5', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.85rem' }}>
              <BookMarked size={22} />
            </div>
            <h3 style={{ fontSize: '0.98rem', fontWeight: 700, marginBottom: '0.35rem' }}>Statutory Law Grounding</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Cross-references clauses against 1,138 indexed sections from the Indian Contract Act 1872, IPC 1860, and Constitution of India.
            </p>
          </div>
        </div>
      </div>

      {/* Recent History */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
          <div className="section-heading" style={{ marginBottom: 0 }}>Recent Contract Evaluations</div>
          {history.length > 0 && (
            <button className="btn btn-secondary" onClick={onClearHistory} style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}>
              <Trash2 size={13} />
              Clear History
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem', background: '#FFFFFF' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem auto', color: 'var(--text-muted)' }}>
              <Clock size={24} />
            </div>
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>No Analysis History Yet</h4>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Upload your first agreement to generate an interactive 2D graph, risk breakdown, and legal advisory.
            </p>
            <button className="btn btn-primary" onClick={onNewAnalysis}>
              <FileSearch size={16} />
              Upload Contract
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {history.map((item) => (
              <div key={item.id} className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.85rem 1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)' }}>
                    <FileText size={18} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)' }}>{item.fileName}</div>
                    <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.65rem', marginTop: '0.15rem' }}>
                      <span><Clock size={12} style={{ display: 'inline', marginRight: '0.25rem' }} />{item.timestamp}</span>
                      <span>•</span>
                      <span>{item.clauseCount} clauses</span>
                      <span>•</span>
                      <span>{item.contradictionCount} contradictions</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                  <span className={`pill pill-${item.overallRisk === 'HIGH' ? 'high' : item.overallRisk === 'MEDIUM' ? 'med' : 'low'}`}>
                    {item.overallRisk === 'HIGH' ? <AlertTriangle size={13} /> : <CheckCircle2 size={13} />}
                    {item.overallRisk} RISK
                  </span>

                  <button className="btn btn-secondary" onClick={() => onSelectContract(item.result)} style={{ padding: '0.45rem 0.85rem', fontSize: '0.82rem' }}>
                    View Report
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
