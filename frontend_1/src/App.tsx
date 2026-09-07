import React, { useState, useEffect } from 'react';
import { Sidebar, type NavPage } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { DashboardPage } from './components/dashboard/DashboardPage';
import { UploadLanding } from './components/analyze/UploadLanding';
import { LoadingOverlay } from './components/analyze/LoadingOverlay';
import { ResultsDashboard } from './components/analyze/ResultsDashboard';
import { LawLibraryPage } from './components/library/LawLibraryPage';
import { SettingsPage } from './components/settings/SettingsPage';
import { uploadContract, analyzeContract } from './services/api';
import type { 
  AnalyzeContractResponse, 
  AnalysisHistoryItem, 
  AppSettings 
} from './types/contract';
import { getOverallRisk } from './utils/formatters';

const DEFAULT_SETTINGS: AppSettings = {
  fastMode: true,
  highThreshold: 0.72,
  mediumThreshold: 0.58,
};

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<NavPage>('dashboard');
  const [activeResult, setActiveResult] = useState<AnalyzeContractResponse | null>(null);
  const [activeFileName, setActiveFileName] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Settings State with LocalStorage
  const [settings, setSettings] = useState<AppSettings>(() => {
    try {
      const saved = localStorage.getItem('contractlens_settings');
      return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  // History State with LocalStorage
  const [history, setHistory] = useState<AnalysisHistoryItem[]>(() => {
    try {
      const saved = localStorage.getItem('contractlens_history');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem('contractlens_settings', JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    localStorage.setItem('contractlens_history', JSON.stringify(history));
  }, [history]);

  const handleUpdateSettings = (updated: Partial<AppSettings>) => {
    setSettings((prev) => ({ ...prev, ...updated }));
  };

  const handleClearHistory = () => {
    setHistory([]);
    localStorage.removeItem('contractlens_history');
  };

  const handleClearSession = () => {
    setActiveResult(null);
    setActiveFileName('');
    handleClearHistory();
    setSettings(DEFAULT_SETTINGS);
  };

  const handleAnalyzeFile = async (file: File) => {
    setIsLoading(true);
    setErrorMessage(null);
    setActiveFileName(file.name);

    try {
      // 1. Upload contract to backend
      const uploadRes = await uploadContract(file);
      const contractPath = uploadRes.json_path || uploadRes.stored_path;

      // 2. Run full pipeline analysis
      const analysisRes = await analyzeContract({
        contractPath,
        fastMode: settings.fastMode,
        highThreshold: settings.highThreshold,
      });

      setActiveResult(analysisRes);
      setActivePage('analyze');

      // 3. Save to history
      const overall = getOverallRisk(analysisRes.risks, settings.highThreshold, settings.mediumThreshold);
      const newHistoryItem: AnalysisHistoryItem = {
        id: uploadRes.contract_id,
        fileName: file.name,
        timestamp: new Date().toLocaleDateString('en-GB', {
          day: 'numeric',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        }),
        overallRisk: overall,
        clauseCount: analysisRes.clauses.length,
        contradictionCount: analysisRes.internal_contradictions.length,
        result: analysisRes,
      };

      setHistory((prev) => [newHistoryItem, ...prev.slice(0, 19)]);
    } catch (err: any) {
      console.error('Analysis error:', err);
      setErrorMessage(err.message || 'Contract analysis failed. Please verify the backend service.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectFromHistory = (result: AnalyzeContractResponse) => {
    setActiveResult(result);
    setActivePage('analyze');
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar activePage={activePage} onNavigate={(p) => setActivePage(p)} />

      {/* Main Content Area */}
      <div className="main-content">
        <Header
          activePage={activePage}
          fastMode={settings.fastMode}
          onStartAnalysis={() => {
            setActiveResult(null);
            setActivePage('analyze');
          }}
        />

        <main className="page-body">
          {/* Error Alert */}
          {errorMessage && (
            <div style={{ marginBottom: '1.25rem', padding: '1rem 1.25rem', background: '#FEE2E2', border: '1px solid #FCA5A5', color: '#991B1B', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>⚠ <strong>Error:</strong> {errorMessage}</span>
              <button
                className="btn btn-secondary"
                onClick={() => setErrorMessage(null)}
                style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Page Routing */}
          {activePage === 'dashboard' && (
            <DashboardPage
              history={history}
              onSelectContract={handleSelectFromHistory}
              onNewAnalysis={() => {
                setActiveResult(null);
                setActivePage('analyze');
              }}
              onClearHistory={handleClearHistory}
            />
          )}

          {activePage === 'analyze' && (
            <>
              {isLoading ? (
                <LoadingOverlay />
              ) : activeResult ? (
                <ResultsDashboard
                  result={activeResult}
                  fileName={activeFileName}
                  highThreshold={settings.highThreshold}
                  mediumThreshold={settings.mediumThreshold}
                  onReset={() => setActiveResult(null)}
                />
              ) : (
                <UploadLanding
                  fastMode={settings.fastMode}
                  onAnalyze={handleAnalyzeFile}
                  isLoading={isLoading}
                />
              )}
            </>
          )}

          {activePage === 'library' && <LawLibraryPage />}

          {activePage === 'settings' && (
            <SettingsPage
              settings={settings}
              onUpdateSettings={handleUpdateSettings}
              onClearSession={handleClearSession}
            />
          )}
        </main>
      </div>
    </div>
  );
};
