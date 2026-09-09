import React from 'react';
import { GitFork, ArrowRight } from 'lucide-react';
import { SchemaRelationship } from '../../types';
import { Card } from '../ui/Card';

export interface RelationshipGraphProps {
  relationships: SchemaRelationship[];
}

export const RelationshipGraph: React.FC<RelationshipGraphProps> = ({ relationships }) => {
  return (
    <Card className="p-4 bg-slate-900/80 border border-slate-800 space-y-3">
      <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
        <GitFork className="w-3.5 h-3.5 text-cyan-400" />
        <span>Foreign Key & Entity Relationships</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
        {relationships.map((rel) => (
          <div
            key={rel.id}
            className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 text-xs flex items-center justify-between group hover:border-slate-700 transition-colors"
          >
            <div className="space-y-0.5 min-w-0">
              <span className="font-mono font-medium text-slate-200 block truncate">
                {rel.sourceTable}.{rel.sourceColumn}
              </span>
              <span className="text-[10px] text-slate-500 uppercase">{rel.type}</span>
            </div>

            <ArrowRight className="w-4 h-4 text-cyan-400 mx-2 flex-shrink-0" />

            <div className="space-y-0.5 text-right min-w-0">
              <span className="font-mono font-medium text-slate-200 block truncate">
                {rel.targetTable}.{rel.targetColumn}
              </span>
              <span className="text-[10px] text-cyan-400/80">Referenced</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
