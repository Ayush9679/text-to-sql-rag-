import React, { ChangeEvent, useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, FileSpreadsheet, UploadCloud, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { getCsrfToken } from '../../services/auth';

interface UploadedColumn {
  original_name: string;
  database_name: string;
  postgres_type: string;
}

interface DatasetUploadResult {
  table_name: string;
  row_count: number;
  columns: UploadedColumn[];
}

export interface DatasetSummary {
  table_name: string;
  row_count?: number;
  created_at?: string;
}

interface DatasetUploadPanelProps {
  datasets: DatasetSummary[];
  isLoadingDatasets?: boolean;
  datasetsError?: string | null;
  onUploadComplete: () => Promise<void> | void;
}

const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export const DatasetUploadPanel: React.FC<DatasetUploadPanelProps> = ({ datasets, isLoadingDatasets = false, datasetsError, onUploadComplete }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DatasetUploadResult | null>(null);

  const resetSelection = () => {
    setFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    setResult(null);
    setError(null);
    if (!selected) {
      setFile(null);
      return;
    }
    if (!selected.name.toLowerCase().endsWith('.csv')) {
      setFile(null);
      setError('Choose a CSV file (.csv) to upload.');
      event.target.value = '';
      return;
    }
    setFile(selected);
  };

  const upload = async () => {
    if (!file) {
      setError('Select a CSV file before uploading.');
      return;
    }
    setIsUploading(true);
    setError(null);
    setResult(null);
    try {
      const csvText = await file.text();
      const response = await fetch(`${apiBaseUrl}/datasets/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(getCsrfToken() ? { 'X-CSRF-Token': getCsrfToken() as string } : {}) },
        body: JSON.stringify({ filename: file.name, csv_text: csvText }),
        credentials: 'include',
      });
      const body: unknown = await response.json().catch(() => null);
      if (!response.ok || !body || typeof body !== 'object') {
        const message = body && typeof body === 'object' && 'error' in body && typeof body.error === 'string'
          ? body.error
          : 'Dataset upload failed. Please check the file and try again.';
        throw new Error(message);
      }
      const uploaded = body as DatasetUploadResult;
      setResult(uploaded);
      await onUploadComplete();
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Dataset upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card variant="outline" className="mb-4 overflow-hidden border-slate-700/80 bg-slate-900/35 shadow-sm">
      <div className="flex flex-col gap-3 px-3.5 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-cyan-500/20 bg-cyan-500/10">
            <FileSpreadsheet className="h-4 w-4 text-cyan-300" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <h2 className="text-sm font-semibold text-slate-100">Dataset intake</h2>
            </div>
            <p className="mt-0.5 text-xs text-slate-400">Load one CSV into this workspace for analysis.</p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <input ref={inputRef} id="dataset-csv" type="file" accept=".csv,text/csv" className="sr-only" onChange={selectFile} />
          <Button variant="outline" size="sm" type="button" onClick={() => inputRef.current?.click()} disabled={isUploading}>
            <FileSpreadsheet className="h-3.5 w-3.5" aria-hidden="true" />
            Choose CSV
          </Button>
          <Button size="sm" type="button" isLoading={isUploading} onClick={upload} disabled={!file} className="bg-indigo-600 hover:bg-indigo-500">
            {!isUploading && <UploadCloud className="h-3.5 w-3.5" aria-hidden="true" />}
            {isUploading ? 'Loading dataset' : 'Upload'}
          </Button>
        </div>
      </div>

      {file && (
        <div className="flex items-center justify-between gap-3 border-t border-slate-800/90 bg-slate-950/30 px-3.5 py-2 text-xs">
          <span className="min-w-0 truncate text-slate-300"><span className="text-slate-500">Ready:</span> {file.name}</span>
          <button type="button" onClick={resetSelection} disabled={isUploading} className="rounded p-1 text-slate-500 transition-colors hover:bg-slate-800 hover:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50" aria-label="Remove selected CSV">
            <X className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      )}

      {error && (
        <div role="alert" className="flex items-start gap-2 border-t border-rose-500/20 bg-rose-500/5 px-3.5 py-2.5 text-xs text-rose-200">
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-400" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="border-t border-emerald-500/15 bg-emerald-500/[0.035] px-3.5 py-3">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" aria-hidden="true" />
            <span className="font-medium text-emerald-200">Table <code className="rounded bg-emerald-950/60 px-1 py-0.5 text-emerald-100">{result.table_name}</code> is ready</span>
            <span className="text-slate-500">{result.row_count.toLocaleString()} rows</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5" aria-label="Detected CSV columns">
            {result.columns.map((column) => (
              <span key={column.database_name} title={`${column.original_name} → ${column.database_name}`} className="rounded-md border border-slate-700/80 bg-slate-950/50 px-1.5 py-1 font-mono text-[11px] text-slate-300">
                {column.original_name} <span className="text-cyan-400/90">{column.postgres_type}</span>
              </span>
            ))}
          </div>
        </div>
      )}
      <div className="border-t border-slate-800/90 bg-slate-950/20 px-3.5 py-2.5">
        <div className="mb-1.5 flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-slate-500"><span>Workspace datasets</span>{isLoadingDatasets && <span className="normal-case text-cyan-300">Refreshing…</span>}</div>
        {datasetsError ? <p className="text-xs text-rose-300">{datasetsError}</p> : datasets.length ? <div className="flex flex-wrap gap-1.5">{datasets.map((dataset) => <span key={dataset.table_name} className="rounded-md border border-slate-700/80 bg-slate-900 px-1.5 py-1 font-mono text-[11px] text-slate-300">{dataset.table_name}{typeof dataset.row_count === 'number' && <span className="ml-1.5 text-slate-500">{dataset.row_count.toLocaleString()} rows</span>}</span>)}</div> : !isLoadingDatasets && <p className="text-xs text-slate-500">No datasets yet. Upload a CSV to begin.</p>}
      </div>
    </Card>
  );
};
