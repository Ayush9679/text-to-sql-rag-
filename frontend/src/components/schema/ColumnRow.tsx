import React from 'react';
import { Key, Link } from 'lucide-react';
import { ColumnDefinition } from '../../types';
import { Badge } from '../ui/Badge';
import { cn } from '../../utils/cn';

export interface ColumnRowProps {
  column: ColumnDefinition;
}

export const ColumnRow: React.FC<ColumnRowProps> = ({ column }) => {
  return (
    <div className="flex items-center justify-between py-2 px-3 hover:bg-slate-800/40 rounded-lg text-xs transition-colors group">
      <div className="flex items-center space-x-2 min-w-0">
        {column.isPrimaryKey ? (
          <span title="Primary Key" className="text-amber-400">
            <Key className="w-3.5 h-3.5 flex-shrink-0" />
          </span>
        ) : column.isForeignKey ? (
          <span title={`Foreign Key -> ${column.foreignKeyTarget?.table}.${column.foreignKeyTarget?.column}`} className="text-cyan-400">
            <Link className="w-3.5 h-3.5 flex-shrink-0" />
          </span>
        ) : (
          <span className="w-3.5 h-3.5 flex-shrink-0" />
        )}

        <span className={cn('font-mono font-medium truncate', column.isPrimaryKey ? 'text-amber-300 font-semibold' : 'text-slate-200')}>
          {column.name}
        </span>

        {!column.isNullable && (
          <span className="text-[10px] text-slate-500 font-mono" title="NOT NULL">*</span>
        )}
      </div>

      <div className="flex items-center space-x-2 flex-shrink-0">
        <span className="font-mono text-[11px] text-indigo-400/90 bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20">
          {column.type}
        </span>

        {column.isForeignKey && column.foreignKeyTarget && (
          <Badge variant="cyan" size="sm" className="hidden sm:inline-flex text-[10px]">
            → {column.foreignKeyTarget.table}
          </Badge>
        )}
      </div>
    </div>
  );
};
