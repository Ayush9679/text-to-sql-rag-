import React from 'react';
import { Database, Sparkles, Shield, Cpu } from 'lucide-react';
import { QuerySuggestions } from './QuerySuggestions';

export interface EmptyStateProps {
  onSelectSuggestion: (query: string) => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectSuggestion }) => {
  return (
    <div className="max-w-2xl mx-auto py-8 px-4 flex flex-col items-center text-center space-y-6">
      <div className="relative">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 border border-indigo-500/30 flex items-center justify-center shadow-glow-primary">
          <Database className="w-8 h-8 text-indigo-400" />
        </div>
        <div className="absolute -top-1 -right-1 p-1 bg-indigo-600 rounded-full border border-slate-900 text-white">
          <Sparkles className="w-3 h-3" />
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
          Conversational Database Analyst
        </h2>
        <p className="text-sm text-slate-400 max-w-lg leading-relaxed">
          Ask questions in natural English to automatically generate optimized SQL queries, inspect confidence breakdowns, and explore analytics.
        </p>
      </div>

      {/* Feature Pills */}
      <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-slate-400">
        <div className="flex items-center space-x-1.5 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-full">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>Multi-Dialect SQL</span>
        </div>
        <div className="flex items-center space-x-1.5 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-full">
          <Shield className="w-3.5 h-3.5 text-emerald-400" />
          <span>Read-Only Guardrails</span>
        </div>
        <div className="flex items-center space-x-1.5 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-full">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Confidence Scoring</span>
        </div>
      </div>

      <div className="w-full text-left pt-4">
        <QuerySuggestions onSelectSuggestion={onSelectSuggestion} />
      </div>
    </div>
  );
};
