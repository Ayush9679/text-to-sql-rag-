import React from 'react';
import { Sparkles, FileText } from 'lucide-react';
import { RetrievedContextItem } from '../../types';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';

export interface RetrievedContextViewerProps {
  items: RetrievedContextItem[];
}

export const RetrievedContextViewer: React.FC<RetrievedContextViewerProps> = ({ items }) => {
  return (
    <Card className="p-4 bg-slate-900/80 border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>Vector RAG Retrieved Context Chunks</span>
        </div>
        <Badge variant="purple" size="sm">Top {items.length} Chunks</Badge>
      </div>

      <div className="space-y-2.5">
        {items.map((item) => (
          <div
            key={item.id}
            className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1.5"
          >
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1.5 font-medium text-slate-200">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                <span>{item.docTitle}</span>
              </div>
              <span className="text-purple-400 font-mono text-[11px] font-semibold">
                Cosine Similarity: {(item.similarity * 100).toFixed(1)}%
              </span>
            </div>

            <p className="text-xs text-slate-400 font-mono bg-slate-900/50 p-2 rounded border border-slate-800/80">
              {item.snippet}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
};
