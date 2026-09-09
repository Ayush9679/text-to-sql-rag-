import React, { useState } from 'react';
import { Table, ChevronDown, ChevronUp, Rows } from 'lucide-react';
import { TableDefinition } from '../../types';
import { ColumnRow } from './ColumnRow';
import { Card } from '../ui/Card';
import { formatNumber } from '../../utils/formatters';
import { cn } from '../../utils/cn';

export interface TableCardProps {
  table: TableDefinition;
  isSelected?: boolean;
  onSelect?: () => void;
}

export const TableCard: React.FC<TableCardProps> = ({
  table,
  isSelected = false,
  onSelect,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <Card
      className={cn(
        'overflow-hidden transition-all duration-200 bg-slate-900/80',
        isSelected ? 'ring-2 ring-indigo-500 border-indigo-500/60 shadow-glow-primary' : 'border-slate-800'
      )}
    >
      <div
        onClick={() => {
          onSelect?.();
          setIsExpanded(!isExpanded);
        }}
        className="p-4 bg-slate-900 hover:bg-slate-850 cursor-pointer flex items-center justify-between border-b border-slate-800"
      >
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
            <Table className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h4 className="text-sm font-semibold text-white font-mono">{table.name}</h4>
              <span className="text-[10px] text-slate-500 font-mono">({table.schema})</span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{table.description}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400">
          <div className="flex items-center space-x-1 font-mono text-[11px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
            <Rows className="w-3 h-3 text-slate-500" />
            <span>{formatNumber(table.rowCount)} rows</span>
          </div>
          <button className="text-slate-500 hover:text-slate-200">
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-3 space-y-1 divide-y divide-slate-800/40 bg-slate-950/40">
          {table.columns.map((col) => (
            <ColumnRow key={col.name} column={col} />
          ))}
        </div>
      )}
    </Card>
  );
};
