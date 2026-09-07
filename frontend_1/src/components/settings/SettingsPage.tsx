import React from 'react';
import { Sliders, Zap, Shield, Cpu, Database, RotateCcw } from 'lucide-react';
import type { AppSettings } from '../../types/contract';

interface SettingsPageProps {
  settings: AppSettings;
  onUpdateSettings: (newSettings: Partial<AppSettings>) => void;
  onClearSession: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  settings,
  onUpdateSettings,
  onClearSession,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '780px' }}>
      {/* Analysis Controls */}
      <div className="card">
        <div className="section-heading">Analysis &amp; Performance Controls</div>

        {/* Fast Mode Toggle */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.85rem 0', borderBottom: '1px solid var(--border-color)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 600, fontSize: '0.92rem' }}>
              <Zap size={16} color="var(--accent)" />
              <span>Fast Mode (~15-20s Execution)</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Bounds law checks to top 6 candidates and generates one LLM explanation for the highest-risk clause for rapid review.
            </p>
          </div>

          <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.fastMode}
              onChange={(e) => onUpdateSettings({ fastMode: e.target.checked })}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: settings.fastMode ? 'var(--accent)' : '#CBD5E1',
                borderRadius: '24px',
                transition: '0.2s',
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  content: '',
                  height: '18px',
                  width: '18px',
                  left: settings.fastMode ? '22px' : '3px',
                  bottom: '3px',
                  backgroundColor: 'white',
                  borderRadius: '50%',
                  transition: '0.2s',
                }}
              />
            </span>
          </label>
        </div>

        {/* High Risk Slider */}
        <div style={{ padding: '1rem 0', borderBottom: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
            <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>High Risk Threshold</span>
            <span className="pill pill-high">Score &ge; {settings.highThreshold.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.50"
            max="0.95"
            step="0.01"
            value={settings.highThreshold}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              onUpdateSettings({
                highThreshold: val,
                mediumThreshold: Math.min(settings.mediumThreshold, val - 0.05),
              });
            }}
            style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            <span>0.50 (Permissive)</span>
            <span>Default: 0.72</span>
            <span>0.95 (Strict)</span>
          </div>
        </div>

        {/* Medium Risk Slider */}
        <div style={{ padding: '1rem 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
            <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>Medium Risk Threshold</span>
            <span className="pill pill-med">Score &ge; {settings.mediumThreshold.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.30"
            max="0.85"
            step="0.01"
            value={settings.mediumThreshold}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              onUpdateSettings({
                mediumThreshold: Math.min(val, settings.highThreshold - 0.05),
              });
            }}
            style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            <span>0.30 (Permissive)</span>
            <span>Default: 0.58</span>
            <span>0.85 (Strict)</span>
          </div>
        </div>
      </div>

      {/* Model & Runtime Architecture Card */}
      <div className="card">
        <div className="section-heading">Active Pipeline Architecture</div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.86rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: 'var(--text-secondary)' }}>
              <Cpu size={16} /> Domain Embedding Model
            </span>
            <strong>law-ai/InLegalBERT (768-d)</strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.86rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: 'var(--text-secondary)' }}>
              <Database size={16} /> Vector Database
            </span>
            <strong>Backend-managed Qdrant Cloud</strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.86rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: 'var(--text-secondary)' }}>
              <Shield size={16} /> Local LLM Runtime
            </span>
            <strong>Ollama (gemma2:2b / llama3.2)</strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', fontSize: '0.86rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: 'var(--text-secondary)' }}>
              <Sliders size={16} /> Document Graph Engine
            </span>
            <strong>NetworkX + ForceAtlas2 Physics</strong>
          </div>
        </div>
      </div>

      {/* Session Management */}
      <div className="card">
        <div className="section-heading">Session Management</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Reset your cached contract analysis results and clear local history stored in your browser.
        </p>

        <button className="btn btn-danger" onClick={onClearSession}>
          <RotateCcw size={16} />
          Clear All Session History
        </button>
      </div>
    </div>
  );
};
