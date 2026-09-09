import React, { useState, useRef, useEffect } from 'react';
import { Download, FileSpreadsheet, FileText, Code2, ChevronDown } from 'lucide-react';
import { Button } from '../ui/Button';

export interface ExportDropdownProps {
  onExportCsv?: () => void;
  onExportJson?: () => void;
}

export const ExportDropdown: React.FC<ExportDropdownProps> = ({
  onExportCsv,
  onExportJson,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="h-8 text-xs px-2.5 text-slate-300"
      >
        <Download className="w-3.5 h-3.5 mr-1 text-slate-400" />
        <span>Export</span>
        <ChevronDown className="w-3 h-3 ml-1 text-slate-400" />
      </Button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-44 rounded-xl bg-slate-900 border border-slate-700/80 shadow-2xl z-30 py-1 animate-fade-in">
          <button
            onClick={() => {
              onExportCsv?.();
              setIsOpen(false);
            }}
            className="w-full flex items-center px-3 py-2 text-xs text-slate-300 hover:bg-slate-800/80 hover:text-white"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 mr-2 text-emerald-400" />
            <span>Export as CSV</span>
          </button>

          <button
            onClick={() => {
              onExportJson?.();
              setIsOpen(false);
            }}
            className="w-full flex items-center px-3 py-2 text-xs text-slate-300 hover:bg-slate-800/80 hover:text-white"
          >
            <Code2 className="w-3.5 h-3.5 mr-2 text-indigo-400" />
            <span>Export as JSON</span>
          </button>

          <button
            onClick={() => setIsOpen(false)}
            className="w-full flex items-center px-3 py-2 text-xs text-slate-300 hover:bg-slate-800/80 hover:text-white"
          >
            <FileText className="w-3.5 h-3.5 mr-2 text-cyan-400" />
            <span>Copy Markdown Table</span>
          </button>
        </div>
      )}
    </div>
  );
};
