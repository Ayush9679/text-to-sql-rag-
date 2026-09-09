import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

export interface LoadingStateProps {
  stage?: 'translating' | 'checking_schema' | 'generating_sql' | 'executing';
}

export const LoadingState: React.FC<LoadingStateProps> = () => {
  const stages = [
    { key: 'translating', label: 'Understanding natural language intent...' },
    { key: 'checking_schema', label: 'Grounding with schema & business rules...' },
    { key: 'generating_sql', label: 'Synthesizing optimized SQL query...' },
    { key: 'executing', label: 'Validating AST & computing confidence score...' },
  ];

  return (
    <div className="flex items-start space-x-3.5 p-4 sm:p-5 bg-slate-900/40 rounded-2xl border border-slate-800/80 animate-pulse-subtle">
      <div className="p-2.5 bg-indigo-600/10 border border-indigo-500/30 rounded-xl text-indigo-400">
        <Bot className="w-5 h-5 animate-spin" />
      </div>

      <div className="space-y-3 flex-1">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">AI Analyst Working</span>
          <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
        </div>

        <div className="space-y-2">
          <div className="h-3.5 bg-slate-800 rounded w-3/4 animate-pulse" />
          <div className="h-3 bg-slate-800/60 rounded w-1/2 animate-pulse" />
        </div>

        <div className="flex flex-wrap gap-2 pt-1">
          {stages.map((s) => (
            <div
              key={s.key}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-800/60 border border-slate-700/50 text-[11px] text-slate-400"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
              <span>{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
