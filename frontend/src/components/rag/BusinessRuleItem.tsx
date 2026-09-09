import React from 'react';
import { ShieldCheck, Table } from 'lucide-react';
import { BusinessRule } from '../../types';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';

export interface BusinessRuleItemProps {
  rule: BusinessRule;
}

export const BusinessRuleItem: React.FC<BusinessRuleItemProps> = ({ rule }) => {
  return (
    <Card className="p-4 bg-slate-900/80 border border-slate-800 space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h4 className="text-sm font-semibold text-white">{rule.name}</h4>
        </div>
        <Badge
          variant={rule.priority === 'high' ? 'danger' : rule.priority === 'medium' ? 'warning' : 'default'}
          size="sm"
        >
          {rule.priority.toUpperCase()} PRIORITY
        </Badge>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed">{rule.description}</p>

      <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 font-mono text-xs text-amber-300">
        <code>{rule.conditionFormula}</code>
      </div>

      <div className="flex items-center space-x-2 text-[11px] text-slate-500 pt-1">
        <Table className="w-3 h-3" />
        <span>Applicable Tables:</span>
        {rule.applicableTables.map((tbl) => (
          <span key={tbl} className="font-mono text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded">
            {tbl}
          </span>
        ))}
      </div>
    </Card>
  );
};
