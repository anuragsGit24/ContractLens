import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  X, 
  Sparkles, 
  Scale, 
  ArrowRight 
} from 'lucide-react';

interface UploadLandingProps {
  fastMode: boolean;
  onAnalyze: (file: File) => void;
  isLoading: boolean;
}

export const UploadLanding: React.FC<UploadLandingProps> = ({
  fastMode,
  onAnalyze,
  isLoading,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    setErrorMsg(null);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        setSelectedFile(file);
      } else {
        setErrorMsg('Please upload a valid PDF contract document.');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        setSelectedFile(file);
      } else {
        setErrorMsg('Please upload a valid PDF contract document.');
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMsg('Please select a PDF contract first.');
      return;
    }
    onAnalyze(selectedFile);
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto' }}>
      {/* Hero Header */}
      <div className="upload-hero">
        <div className="hero-badge">
          <Sparkles size={14} />
          <span>Indian Legal AI Engine</span>
        </div>
        <h2 className="hero-title">Instant Legal Risk Analysis</h2>
        <p className="hero-subtitle">
          Upload any Indian business agreement and receive deep clause classification, contradiction alerts, and statutory citations in under 20 seconds.
        </p>

        <div className="trust-row">
          <div className="trust-item">🔒 100% Private &amp; Offline Supported</div>
          <div className="trust-item">⚡ Under 20 Seconds Execution</div>
          <div className="trust-item">📜 Grounded in Indian Law (ICA, IPC, Constitution)</div>
        </div>
      </div>

      {/* Dropzone Container */}
      <form onSubmit={handleSubmit} className="dropzone-container">
        <input
          type="file"
          ref={inputRef}
          onChange={handleFileChange}
          accept=".pdf,application/pdf"
          style={{ display: 'none' }}
        />

        <div
          className={`dropzone ${isDragOver ? 'active' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="dropzone-icon-wrap">
            <UploadCloud size={28} />
          </div>
          <div className="dropzone-prompt">
            {selectedFile ? 'Click or drop another file to replace' : 'Click to upload or drag and drop your PDF'}
          </div>
          <div className="dropzone-hint">Supports standard &amp; scanned PDF business contracts up to 25MB</div>
        </div>

        {errorMsg && (
          <div style={{ marginTop: '0.75rem', padding: '0.65rem 1rem', background: '#FEE2E2', border: '1px solid #FCA5A5', color: '#991B1B', borderRadius: 'var(--radius-md)', fontSize: '0.84rem' }}>
            ⚠ {errorMsg}
          </div>
        )}

        {/* Selected File Card */}
        {selectedFile && (
          <div className="selected-file-card">
            <div className="file-info">
              <FileText size={20} color="var(--accent)" />
              <div>
                <div style={{ color: 'var(--text-primary)' }}>{selectedFile.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {(selectedFile.size / 1024).toFixed(1)} KB • PDF Document
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
              }}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '0.25rem' }}
              title="Remove file"
            >
              <X size={18} />
            </button>
          </div>
        )}

        {/* Action Button */}
        <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!selectedFile || isLoading}
            style={{ width: '100%', padding: '0.85rem', fontSize: '0.98rem' }}
          >
            <Scale size={18} />
            {isLoading ? 'Analysing Agreement...' : 'Analyse Contract Now'}
            <ArrowRight size={18} />
          </button>

          {fastMode && (
            <div style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              ⚡ <strong>Fast Mode Enabled:</strong> Explanations prioritised for high-risk clauses for rapid ~15s turnaround.
            </div>
          )}
        </div>
      </form>

      {/* 3 Step Workflow */}
      <div className="steps-grid">
        <div className="step-card">
          <div className="step-number">1</div>
          <div className="step-title">1. Upload Agreement</div>
          <div className="step-desc">PyMuPDF and Tesseract OCR segment document into clean legal clauses.</div>
        </div>

        <div className="step-card">
          <div className="step-number">2</div>
          <div className="step-title">2. AI Clause Screening</div>
          <div className="step-desc">InLegalBERT vector graph scans for intra-document conflicts and risk factors.</div>
        </div>

        <div className="step-card">
          <div className="step-number">3</div>
          <div className="step-title">3. Statutory Grounding</div>
          <div className="step-desc">Cross-references Qdrant legal database with verified Ollama LLM explanations.</div>
        </div>
      </div>
    </div>
  );
};
