import React from 'react';
import { ArrowRight, BookMarked } from 'lucide-react';
import { SynonymMapping } from '../../types';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';

export interface TermSynonymListProps {
  synonyms: SynonymMapping[];
}

export const TermSynonymList: React.FC<TermSynonymListProps> = ({ synonyms }) => {
  return (
    <Card className="p-4 bg-slate-900/80 border border-slate-800 space-y-3">
      <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
        <BookMarked className="w-4 h-4 text-cyan-400" />
        <span>Domain Synonyms & Vocabulary Mappings</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {synonyms.map((s) => (
          <div
            key={s.id}
            className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs flex items-center justify-between"
          >
            <div className="space-y-0.5">
              <span className="font-semibold text-slate-200 block">"{s.userTerm}"</span>
              <span className="text-[10px] text-slate-500">{s.context}</span>
            </div>

            <ArrowRight className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mx-2" />

            <div className="text-right space-y-0.5">
              <span className="font-mono text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20 block">
                {s.canonicalEntity}
              </span>
              <Badge variant="cyan" size="sm" className="text-[9px]">
                {s.targetType}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
