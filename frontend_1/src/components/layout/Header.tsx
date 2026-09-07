import React from 'react';
import { Zap, ShieldCheck, FilePlus } from 'lucide-react';
import type { NavPage } from './Sidebar';

interface HeaderProps {
  activePage: NavPage;
  fastMode: boolean;
  onStartAnalysis: () => void;
}

const PAGE_TITLES: Record<NavPage, { title: string; subtitle: string }> = {
  dashboard: {
    title: 'Executive Dashboard',
    subtitle: 'Overview of legal risk metrics and recent contract evaluations',
  },
  analyze: {
    title: 'Contract Analysis Studio',
    subtitle: 'Upload agreements for automated clause classification, contradiction scanning, and statutory grounding',
  },
  library: {
    title: 'Indian Statutory Knowledge Base',
    subtitle: 'Indexed Indian statutes, penal provisions, and constitutional articles',
  },
  settings: {
    title: 'Analysis & Model Settings',
    subtitle: 'Fine-tune risk scoring thresholds, Fast Mode bounds, and execution parameters',
  },
};

export const Header: React.FC<HeaderProps> = ({ activePage, fastMode, onStartAnalysis }) => {
  const info = PAGE_TITLES[activePage];

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div>
          <h1 className="topbar-title">{info.title}</h1>
        </div>
      </div>

      <div className="topbar-right">
        {fastMode && (
          <span className="pill pill-info" title="Fast Mode limits law checks and explanations for <20s analysis">
            <Zap size={13} />
            Fast Mode Active
          </span>
        )}

        <span className="pill pill-low">
          <ShieldCheck size={13} />
          InLegalBERT Engine
        </span>

        {activePage !== 'analyze' && (
          <button className="btn btn-primary" onClick={onStartAnalysis} style={{ padding: '0.45rem 0.95rem', fontSize: '0.82rem' }}>
            <FilePlus size={15} />
            Analyse Contract
          </button>
        )}
      </div>
    </header>
  );
};
