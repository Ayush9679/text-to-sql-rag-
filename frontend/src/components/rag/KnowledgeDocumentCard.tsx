import React from 'react';
import { BookOpen, Tag, Calendar, Sparkles } from 'lucide-react';
import { KnowledgeDocument } from '../../types';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';

export interface KnowledgeDocumentCardProps {
  doc: KnowledgeDocument;
}

export const KnowledgeDocumentCard: React.FC<KnowledgeDocumentCardProps> = ({ doc }) => {
  return (
    <Card className="p-4 bg-slate-900/80 border border-slate-800 space-y-3 hover:border-indigo-500/30 transition-all">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">{doc.title}</h4>
            <div className="flex items-center space-x-2 mt-0.5 text-[11px] text-slate-500">
              <span>Source: {doc.source}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" /> {doc.updatedAt}
              </span>
            </div>
          </div>
        </div>

        {doc.relevanceScore !== undefined && (
          <Badge variant="purple" size="sm">
            <Sparkles className="w-3 h-3 mr-1" />
            {Math.round(doc.relevanceScore * 100)}% Match
          </Badge>
        )}
      </div>

      <p className="text-xs text-slate-300 bg-slate-950/40 p-3 rounded-lg border border-slate-800/60 leading-relaxed font-mono">
        {doc.content}
      </p>

      <div className="flex flex-wrap items-center gap-1.5 pt-1">
        <Tag className="w-3 h-3 text-slate-500 mr-1" />
        {doc.tags.map((tag) => (
          <span
            key={tag}
            className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full border border-slate-700/60"
          >
            #{tag}
          </span>
        ))}
      </div>
    </Card>
  );
};
