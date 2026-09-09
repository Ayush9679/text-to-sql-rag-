import React from 'react';
import { Database, Table } from 'lucide-react';
import { DatabaseSchema } from '../../types';
import { cn } from '../../utils/cn';

export interface DatabaseSidebarProps {
  schema: DatabaseSchema;
  selectedTableName?: string;
  onSelectTable: (tableName: string) => void;
}

export const DatabaseSidebar: React.FC<DatabaseSidebarProps> = ({
  schema,
  selectedTableName,
  onSelectTable,
}) => {
  return (
    <div className="w-full md:w-64 flex-shrink-0 bg-slate-900/60 rounded-2xl border border-slate-800 p-4 space-y-4">
      <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-800">
        <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
          <Database className="w-4 h-4" />
        </div>
        <div>
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">{schema.name}</h4>
          <span className="text-[10px] text-slate-500 font-mono">{schema.dialect} v{schema.version}</span>
        </div>
      </div>

      <div className="space-y-1">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-2 block mb-2">
          Tables ({schema.tables.length})
        </span>

        {schema.tables.map((t) => {
          const isSelected = selectedTableName === t.name;
          return (
            <button
              key={t.name}
              onClick={() => onSelectTable(t.name)}
              className={cn(
                'w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-mono transition-all text-left',
                isSelected
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 font-medium'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              )}
            >
              <div className="flex items-center space-x-2 truncate">
                <Table className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                <span className="truncate">{t.name}</span>
              </div>
              <span className="text-[10px] text-slate-500">{t.columns.length} col</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
