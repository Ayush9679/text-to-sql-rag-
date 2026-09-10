'use client';

import React, { useState } from 'react';
import { Table, Copy, Check } from 'lucide-react';

interface ResultsTableProps {
  columns: string[];
  data: Record<string, unknown>[];
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ columns, data }) => {
  const [copied, setCopied] = useState(false);

  if (!data || data.length === 0) {
    return null;
  }

  // Determine headers if not provided
  const tableColumns =
    columns && columns.length > 0
      ? columns
      : Object.keys(data[0] || {});

  const handleCopy = () => {
    const jsonStr = JSON.stringify(data, null, 2);
    navigator.clipboard.writeText(jsonStr);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-2">
          <Table className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">Query Results</h3>
          <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full font-mono">
            {data.length} row{data.length === 1 ? '' : 's'}
          </span>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
          title="Copy data as JSON"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy JSON</span>
            </>
          )}
        </button>
      </div>

      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950 text-slate-400 uppercase font-semibold sticky top-0 border-b border-slate-800">
            <tr>
              {tableColumns.map((col, idx) => (
                <th key={idx} className="px-4 py-3 tracking-wider font-mono">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {data.map((row, rIdx) => (
              <tr
                key={rIdx}
                className="hover:bg-slate-800/40 transition-colors"
              >
                {tableColumns.map((col, cIdx) => {
                  const val = row[col];
                  return (
                    <td key={cIdx} className="px-4 py-2.5 whitespace-nowrap">
                      {val === null || val === undefined ? (
                        <span className="text-slate-600 italic">null</span>
                      ) : typeof val === 'object' ? (
                        JSON.stringify(val)
                      ) : (
                        String(val)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
