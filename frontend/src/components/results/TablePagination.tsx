import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Button } from '../ui/Button';

export interface TablePaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalRows: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
}

export const TablePagination: React.FC<TablePaginationProps> = ({
  currentPage,
  totalPages,
  pageSize,
  totalRows,
  onPageChange,
  onPageSizeChange,
}) => {
  const startRow = (currentPage - 1) * pageSize + 1;
  const endRow = Math.min(currentPage * pageSize, totalRows);

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 bg-slate-900/60 border-t border-slate-800 text-xs text-slate-400">
      <div className="flex items-center space-x-2">
        <span>
          Showing <span className="font-medium text-slate-200">{startRow}</span> to{' '}
          <span className="font-medium text-slate-200">{endRow}</span> of{' '}
          <span className="font-medium text-slate-200">{totalRows}</span> rows
        </span>

        {onPageSizeChange && (
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="ml-2 bg-slate-800 border border-slate-700 text-slate-300 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value={5}>5 / page</option>
            <option value={10}>10 / page</option>
            <option value={25}>25 / page</option>
            <option value={50}>50 / page</option>
          </select>
        )}
      </div>

      <div className="flex items-center space-x-1.5">
        <Button
          variant="outline"
          size="icon"
          className="h-7 w-7 p-0"
          onClick={() => onPageChange(1)}
          disabled={currentPage <= 1}
          aria-label="First Page"
        >
          <ChevronsLeft className="w-3.5 h-3.5" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-7 w-7 p-0"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          aria-label="Previous Page"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
        </Button>

        <span className="px-2 font-medium text-slate-300">
          Page {currentPage} of {Math.max(1, totalPages)}
        </span>

        <Button
          variant="outline"
          size="icon"
          className="h-7 w-7 p-0"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          aria-label="Next Page"
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-7 w-7 p-0"
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage >= totalPages}
          aria-label="Last Page"
        >
          <ChevronsRight className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  );
};
