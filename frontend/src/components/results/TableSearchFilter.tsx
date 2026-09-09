import React from 'react';
import { Search, Filter, X } from 'lucide-react';
import { Input } from '../ui/Input';

export interface TableSearchFilterProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  columnFilter?: string;
  onColumnFilterChange?: (col: string) => void;
  availableColumns?: string[];
}

export const TableSearchFilter: React.FC<TableSearchFilterProps> = ({
  searchTerm,
  onSearchChange,
  columnFilter = 'all',
  onColumnFilterChange,
  availableColumns = [],
}) => {
  return (
    <div className="flex flex-wrap items-center gap-2.5">
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Input
          placeholder="Filter rows..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          leftIcon={<Search className="w-3.5 h-3.5" />}
          rightIcon={
            searchTerm ? (
              <button onClick={() => onSearchChange('')} className="hover:text-slate-200">
                <X className="w-3.5 h-3.5" />
              </button>
            ) : undefined
          }
          className="h-8 text-xs py-1.5"
        />
      </div>

      {availableColumns.length > 0 && onColumnFilterChange && (
        <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1">
          <Filter className="w-3 h-3 text-slate-400" />
          <select
            value={columnFilter}
            onChange={(e) => onColumnFilterChange(e.target.value)}
            aria-label="Filter column"
            className="bg-transparent text-xs text-slate-300 focus:outline-none cursor-pointer"
          >
            <option value="all" className="bg-slate-900">All Columns</option>
            {availableColumns.map((col) => (
              <option key={col} value={col} className="bg-slate-900">
                {col}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
};
