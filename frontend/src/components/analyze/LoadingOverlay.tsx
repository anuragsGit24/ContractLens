import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';

const PIPELINE_STEPS = [
  'Uploading contract document & parsing clauses...',
  'Generating InLegalBERT 768-d embeddings...',
  'Building semantic knowledge graph & calculating cosine density...',
  'Scanning for intra-contract drafting contradictions...',
  'Scoring zero-shot risk categories against Indian commercial law...',
  'Retrieving relevant Indian statutes from Qdrant vector database...',
  'Generating plain-English LLM advisory with citation verification...',
];

export const LoadingOverlay: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev < PIPELINE_STEPS.length - 1 ? prev + 1 : prev));
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="loading-overlay">
      <div className="loading-spinner-wrap">
        <div className="spinner-ring" />
      </div>

      <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
        Analysing Contract
      </h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
        Please wait while ContractLens evaluates clauses against Indian statutes...
      </p>

      <div className="pipeline-steps-list">
        {PIPELINE_STEPS.map((step, idx) => {
          const isDone = idx < currentStep;
          const isActive = idx === currentStep;

          return (
            <div
              key={step}
              className={`pipeline-step-item ${isActive ? 'active' : isDone ? 'completed' : ''}`}
            >
              {isDone ? (
                <CheckCircle2 size={16} color="#166534" />
              ) : isActive ? (
                <Loader2 size={16} className="spin" color="var(--accent)" />
              ) : (
                <Circle size={16} color="var(--text-subtle)" />
              )}
              <span>{step}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
