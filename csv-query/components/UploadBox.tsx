'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, Database, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { Dataset, UploadResponse } from '@/types';

interface UploadBoxProps {
  datasets: Dataset[];
  activeDataset: Dataset | null;
  onSelectDataset: (dataset: Dataset) => void;
  onUploadSuccess: (uploaded: UploadResponse) => void;
}

export const UploadBox: React.FC<UploadBoxProps> = ({
  datasets,
  activeDataset,
  onSelectDataset,
  onUploadSuccess,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.csv') && file.type !== 'text/csv') {
      setUploadError('Please select a valid .csv file.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to upload CSV file.');
      }

      onUploadSuccess(data);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const onFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          Data Source
        </h2>
        {activeDataset && (
          <span className="text-xs bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-2.5 py-1 rounded-full font-medium">
            Active Dataset
          </span>
        )}
      </div>

      {/* Dataset Picker Dropdown if datasets exist */}
      {datasets.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-400">
            Select Previously Uploaded Dataset
          </label>
          <select
            className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-xl px-3.5 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none cursor-pointer"
            value={activeDataset?.id || ''}
            onChange={(e) => {
              const selected = datasets.find((d) => d.id === e.target.value);
              if (selected) onSelectDataset(selected);
            }}
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.row_count} rows)
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Drag and Drop Box */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-3 ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10'
            : 'border-slate-800 hover:border-slate-700 bg-slate-950/50'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={onFileInputChange}
          accept=".csv"
          className="hidden"
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-2 py-4">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
            <p className="text-sm font-medium text-slate-300">
              Parsing & uploading CSV...
            </p>
            <p className="text-xs text-slate-500">
              Generating schema & inserting rows into Postgres
            </p>
          </div>
        ) : (
          <>
            <div className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-slate-500 mt-1">
                CSV files up to 10MB
              </p>
            </div>
          </>
        )}
      </div>

      {/* Error Message */}
      {uploadError && (
        <div className="flex items-start gap-2 bg-rose-500/10 border border-rose-500/20 text-rose-300 p-3 rounded-xl text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Inferred Schema Pill List */}
      {activeDataset && (
        <div className="border-t border-slate-800/80 pt-4 flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              {activeDataset.name}
            </span>
            <span className="text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded">
              {activeDataset.row_count.toLocaleString()} rows
            </span>
          </div>

          <div>
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold mb-2 block">
              Inferred Columns ({activeDataset.columns.length})
            </span>
            <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pr-1">
              {activeDataset.columns.map((col, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-1 bg-slate-950 border border-slate-800 px-2 py-1 rounded-lg text-xs"
                >
                  <span className="text-slate-300 font-medium">{col.name}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                      col.type === 'number'
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : col.type === 'date'
                        ? 'bg-amber-500/10 text-amber-400'
                        : 'bg-blue-500/10 text-blue-400'
                    }`}
                  >
                    {col.type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
