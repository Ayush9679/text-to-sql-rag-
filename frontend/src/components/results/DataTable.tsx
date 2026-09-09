import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Database, Loader2 } from 'lucide-react';
import { QueryResultData } from '../../types';
import { TablePagination } from './TablePagination';
import { TableSearchFilter } from './TableSearchFilter';
import { ExportDropdown } from './ExportDropdown';
import { cn } from '../../utils/cn';

export interface DataTableProps {
  data?: QueryResultData;
  isLoading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export const DataTable: React.FC<DataTableProps> = ({
  data,
  isLoading = false,
  emptyMessage = 'No query results returned.',
  className,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [columnFilter, setColumnFilter] = useState('all');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const columns = data?.columns || [];
  const rows = data?.rows || [];

  const handleSort = (col: string) => {
    if (sortColumn === col) {
      if (sortDirection === 'asc') setSortDirection('desc');
      else {
        setSortColumn(null);
        setSortDirection('asc');
      }
    } else {
      setSortColumn(col);
      setSortDirection('asc');
    }
  };

  const filteredRows = useMemo(() => {
    let result = [...rows];

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter((row) => {
        if (columnFilter !== 'all' && row[columnFilter] !== undefined) {
          return String(row[columnFilter]).toLowerCase().includes(term);
        }
        return Object.values(row).some((val) =>
          String(val).toLowerCase().includes(term)
        );
      });
    }

    if (sortColumn) {
      result.sort((a, b) => {
        const valA = a[sortColumn];
        const valB = b[sortColumn];

        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortDirection === 'asc' ? valA - valB : valB - valA;
        }
        return sortDirection === 'asc'
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA));
      });
    }

    return result;
  }, [rows, searchTerm, columnFilter, sortColumn, sortDirection]);

  const totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, currentPage, pageSize]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-slate-900/60 rounded-xl border border-slate-800 space-y-3">
        <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
        <p className="text-xs text-slate-400 font-medium">Executing SQL and streaming result sets...</p>
      </div>
    );
  }

  if (!data || columns.length === 0 || rows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-10 bg-slate-900/40 rounded-xl border border-slate-800/80 text-center">
        <div className="p-3 bg-slate-800/60 rounded-full text-slate-500 mb-2">
          <Database className="w-5 h-5" />
        </div>
        <p className="text-xs text-slate-400 font-medium">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={cn('rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden shadow-sm', className)}>
      {/* Controls Bar */}
      <div className="p-3 bg-slate-900/70 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <TableSearchFilter
          searchTerm={searchTerm}
          onSearchChange={(term) => {
            setSearchTerm(term);
            setCurrentPage(1);
          }}
          columnFilter={columnFilter}
          onColumnFilterChange={setColumnFilter}
          availableColumns={columns}
        />
        <ExportDropdown />
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-900/90 border-b border-slate-800 text-slate-400 font-mono select-none">
              <th className="py-2.5 px-3 w-10 text-center font-normal text-slate-600">#</th>
              {columns.map((col) => {
                const isSorted = sortColumn === col;
                return (
                  <th
                    key={col}
                    onClick={() => handleSort(col)}
                    className="py-2.5 px-3.5 font-medium hover:text-slate-200 cursor-pointer transition-colors whitespace-nowrap"
                  >
                    <div className="flex items-center space-x-1.5">
                      <span>{col}</span>
                      <span className="text-slate-500">
                        {isSorted ? (
                          sortDirection === 'asc' ? (
                            <ArrowUp className="w-3 h-3 text-indigo-400" />
                          ) : (
                            <ArrowDown className="w-3 h-3 text-indigo-400" />
                          )
                        ) : (
                          <ArrowUpDown className="w-3 h-3 opacity-40 hover:opacity-100" />
                        )}
                      </span>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {paginatedRows.map((row, idx) => {
              const rowIndex = (currentPage - 1) * pageSize + idx + 1;
              return (
                <tr
                  key={idx}
                  className="hover:bg-slate-800/40 transition-colors group text-slate-300"
                >
                  <td className="py-2 px-3 text-center text-slate-600 font-mono text-[11px]">
                    {rowIndex}
                  </td>
                  {columns.map((col) => {
                    const value = row[col];
                    const isNumber = typeof value === 'number';
                    return (
                      <td
                        key={col}
                        className={cn(
                          'py-2 px-3.5 whitespace-nowrap font-mono text-xs',
                          isNumber ? 'text-indigo-300/90' : 'text-slate-300'
                        )}
                      >
                        {value === null || value === undefined ? (
                          <span className="text-slate-600 italic">NULL</span>
                        ) : typeof value === 'boolean' ? (
                          <span
                            className={cn(
                              'px-1.5 py-0.5 rounded text-[10px]',
                              value ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                            )}
                          >
                            {String(value)}
                          </span>
                        ) : (
                          String(value)
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <TablePagination
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        totalRows={filteredRows.length}
        onPageChange={setCurrentPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setCurrentPage(1);
        }}
      />
    </div>
  );
};
