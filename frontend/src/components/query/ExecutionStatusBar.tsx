import React from 'react';
import { ShieldCheck, Activity, Database, Zap } from 'lucide-react';

export const ExecutionStatusBar: React.FC = () => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2 bg-slate-950/80 border-b border-slate-800/80 text-xs text-slate-400">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-slate-300 font-medium flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-indigo-400" /> PostgreSQL Production Replica
          </span>
        </div>

        <div className="hidden sm:flex items-center space-x-1.5 text-slate-500">
          <span>•</span>
          <span className="flex items-center gap-1 text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> AST Guardrails ON
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-3 text-slate-400">
        <div className="flex items-center space-x-1">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span className="font-mono text-[11px]">Groq Llama-3-70b (Preview)</span>
        </div>
        <div className="flex items-center space-x-1 hidden md:flex">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-mono text-[11px]">Latency: 142ms</span>
        </div>
      </div>
    </div>
  );
};
