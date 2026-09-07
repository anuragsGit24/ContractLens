import React, { useState, useEffect } from 'react';
import { 
  Scale, 
  LayoutDashboard, 
  FileText, 
  BookOpen, 
  Settings, 
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { checkHealth } from '../../services/api';

export type NavPage = 'dashboard' | 'analyze' | 'library' | 'settings';

interface SidebarProps {
  activePage: NavPage;
  onNavigate: (page: NavPage) => void;
}

const LEGAL_TIPS = [
  "Section 27 of the Indian Contract Act renders most post-employment non-compete clauses void and unenforceable.",
  "Uncapped indemnity clauses can expose small businesses to unlimited downstream and third-party liabilities.",
  "Always verify dispute resolution seat and governing law clauses to ensure Indian jurisdiction compatibility.",
  "Liquidated damages under Section 74 must represent a genuine pre-estimate of loss rather than punitive penalties.",
  "Force majeure provisions should clearly define excusable delays, notice timelines, and mitigation duties."
];

export const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate }) => {
  const [backendStatus, setBackendStatus] = useState<'up' | 'warn' | 'down'>('up');
  const [tipIndex, setTipIndex] = useState(0);

  useEffect(() => {
    // Pick random tip on mount
    setTipIndex(Math.floor(Math.random() * LEGAL_TIPS.length));

    const pollHealth = async () => {
      try {
        await checkHealth();
        setBackendStatus('up');
      } catch {
        setBackendStatus('down');
      }
    };

    pollHealth();
    const timer = setInterval(pollHealth, 15000);
    return () => clearInterval(timer);
  }, []);

  const cycleTip = () => {
    setTipIndex((prev) => (prev + 1) % LEGAL_TIPS.length);
  };

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-logo-row">
          <div className="brand-icon-wrap">
            <Scale size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span className="brand-title">ContractLens</span>
              <span className="brand-badge">AI</span>
            </div>
            <p className="brand-subtitle">Indian Legal Intelligence</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        
        <button
          className={`nav-button ${activePage === 'dashboard' ? 'active' : ''}`}
          onClick={() => onNavigate('dashboard')}
        >
          <LayoutDashboard size={18} className="nav-icon" />
          <span>Dashboard</span>
        </button>

        <button
          className={`nav-button ${activePage === 'analyze' ? 'active' : ''}`}
          onClick={() => onNavigate('analyze')}
        >
          <FileText size={18} className="nav-icon" />
          <span>Analyse Contract</span>
        </button>

        <button
          className={`nav-button ${activePage === 'library' ? 'active' : ''}`}
          onClick={() => onNavigate('library')}
        >
          <BookOpen size={18} className="nav-icon" />
          <span>Law Library</span>
        </button>

        <button
          className={`nav-button ${activePage === 'settings' ? 'active' : ''}`}
          onClick={() => onNavigate('settings')}
        >
          <Settings size={18} className="nav-icon" />
          <span>Settings</span>
        </button>
      </nav>

      {/* Footer Widgets */}
      <div className="sidebar-footer">
        {/* Live Service Status */}
        <div className="status-box">
          <div className="status-header">System Health</div>
          <div className="status-row">
            <span>FastAPI Server</span>
            <span className={`status-dot dot-${backendStatus}`} />
          </div>
          <div className="status-row">
            <span>Vector DB (Qdrant)</span>
            <span className="status-dot dot-up" />
          </div>
          <div className="status-row">
            <span>Local LLM (Ollama)</span>
            <span className="status-dot dot-up" />
          </div>
        </div>

        {/* Daily Legal Tip */}
        <div className="tip-card" onClick={cycleTip} title="Click to view another tip">
          <div className="tip-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Sparkles size={12} />
              Legal Insight
            </span>
            <RefreshCw size={11} />
          </div>
          <p className="tip-body">{LEGAL_TIPS[tipIndex]}</p>
        </div>
      </div>
    </aside>
  );
};
