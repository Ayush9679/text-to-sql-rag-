import React from 'react';
import { ConfidenceData } from '../../types';
import { ConfidenceGauge } from './ConfidenceGauge';
import { ConfidenceBadge } from './ConfidenceBadge';

export interface ConfidenceBreakdownProps {
  confidence: ConfidenceData;
}

export const ConfidenceBreakdown: React.FC<ConfidenceBreakdownProps> = ({ confidence }) => {
  const factors = [
    { label: 'Schema Alignment', value: confidence.factors.schemaAlignment, desc: 'Matched table and column entities' },
    { label: 'Intent Clarity', value: confidence.factors.intentClarity, desc: 'Natural language unambiguous request' },
    { label: 'Syntax Validity', value: confidence.factors.syntaxValidity, desc: 'Parsed dialect AST valid structure' },
    { label: 'RAG Grounding', value: confidence.factors.ragGrounding, desc: 'Corroborated with business rules' },
  ];

  return (
    <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ConfidenceGauge score={confidence.score} size={48} strokeWidth={5} />
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">AI Confidence Score</span>
              <ConfidenceBadge score={confidence.score} size="sm" showPercent={false} />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">{confidence.explanation}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80">
        {factors.map((f) => {
          const percent = Math.round(f.value * 100);
          return (
            <div key={f.label} className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800/60">
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-medium text-slate-300">{f.label}</span>
                <span className="font-mono font-semibold text-indigo-400">{percent}%</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${percent}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1 truncate">{f.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
