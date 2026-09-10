'use client';

import React, { useState, useEffect } from 'react';
import { Database, Sparkles, Terminal, AlertCircle, HelpCircle, Code, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';
import { UploadBox } from '@/components/UploadBox';
import { QueryBox } from '@/components/QueryBox';
import { ResultsTable } from '@/components/ResultsTable';
import { ResultsChart } from '@/components/ResultsChart';
import { Dataset, QueryResponse, UploadResponse } from '@/types';

export default function Home() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(null);
  const [isLoadingQuery, setIsLoadingQuery] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [showSql, setShowSql] = useState(false);
  const [sqlCopied, setSqlCopied] = useState(false);
  const [clarificationAnswer, setClarificationAnswer] = useState('');

  // Fetch existing datasets on mount
  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const res = await fetch('/api/datasets');
      if (res.ok) {
        const data = await res.json();
        if (data.datasets && Array.isArray(data.datasets)) {
          setDatasets(data.datasets);
          if (data.datasets.length > 0 && !activeDataset) {
            setActiveDataset(data.datasets[0]);
          }
        }
      }
    } catch (err) {
      console.warn('Failed to load datasets:', err);
    }
  };

  const handleUploadSuccess = (uploaded: UploadResponse) => {
    const newDataset: Dataset = {
      id: uploaded.datasetId,
      name: uploaded.name,
      columns: uploaded.columns,
      row_count: uploaded.rowCount,
      created_at: new Date().toISOString(),
    };

    setDatasets((prev) => [newDataset, ...prev]);
    setActiveDataset(newDataset);
    setQueryResult(null);
    setQueryError(null);
  };

  const handleRunQuery = async (questionText: string) => {
    if (!activeDataset) {
      setQueryError('Please upload or select a dataset first.');
      return;
    }

    setIsLoadingQuery(true);
    setQueryError(null);
    setQueryResult(null);
    setClarificationAnswer('');

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          datasetId: activeDataset.id,
          question: questionText,
        }),
      });

      const data: QueryResponse = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to analyze question.');
      }

      setQueryResult(data);
      if (data.error && !data.answer) {
        setQueryError(data.error);
      }
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : 'Unable to complete query.');
    } finally {
      setIsLoadingQuery(false);
    }
  };

  const handleClarificationSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!clarificationAnswer.trim()) return;
    handleRunQuery(clarificationAnswer.trim());
  };

  const copySqlToClipboard = () => {
    if (!queryResult?.sql) return;
    navigator.clipboard.writeText(queryResult.sql);
    setSqlCopied(true);
    setTimeout(() => setSqlCopied(false), 2000);
  };

  return (
    <main className="min-h-screen bg-[#090D16] text-slate-100 pb-20">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                csv-query
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  AI Text-to-SQL
                </span>
              </h1>
              <p className="text-xs text-slate-400">Natural-language analytics over PostgreSQL JSONB</p>
            </div>
          </div>

          {activeDataset && (
            <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Target:</span>
              <span className="text-white font-medium">{activeDataset.name}</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 flex flex-col gap-8">
        {/* Top Two-Panel Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Panel: Upload & Dataset Selector */}
          <div className="lg:col-span-5">
            <UploadBox
              datasets={datasets}
              activeDataset={activeDataset}
              onSelectDataset={(ds) => {
                setActiveDataset(ds);
                setQueryResult(null);
                setQueryError(null);
              }}
              onUploadSuccess={handleUploadSuccess}
            />
          </div>

          {/* Right Panel: Query Box */}
          <div className="lg:col-span-7">
            <QueryBox
              isLoading={isLoadingQuery}
              disabled={!activeDataset}
              onSubmit={handleRunQuery}
              sampleColumns={activeDataset?.columns.map((c) => c.name) || []}
            />
          </div>
        </div>

        {/* Global Error Alert */}
        {queryError && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-4 rounded-2xl flex items-start gap-3 shadow-lg">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">Query Error</p>
              <p className="text-xs mt-0.5 text-rose-300/90">{queryError}</p>
            </div>
          </div>
        )}

        {/* Results Area */}
        {queryResult && (
          <div className="flex flex-col gap-6 animate-fadeIn">
            {/* Needs Clarification Prompt Banner */}
            {queryResult.needs_clarification && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
                    <HelpCircle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-amber-300">
                      Clarification Needed
                    </h3>
                    <p className="text-sm text-slate-200 mt-1">
                      {queryResult.clarification_question ||
                        'The model needs more context to answer your question accurately.'}
                    </p>
                  </div>
                </div>

                <form onSubmit={handleClarificationSubmit} className="flex gap-2">
                  <input
                    type="text"
                    value={clarificationAnswer}
                    onChange={(e) => setClarificationAnswer(e.target.value)}
                    placeholder="Type your clarification or specific column name..."
                    className="flex-1 bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-amber-500 outline-none"
                  />
                  <button
                    type="submit"
                    className="bg-amber-600 hover:bg-amber-500 text-white font-medium text-xs px-5 py-2.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Submit Clarification
                  </button>
                </form>
              </div>
            )}

            {/* Answer Card */}
            {queryResult.answer && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-3">
                <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
                  <Sparkles className="w-4 h-4" />
                  <span>AI Analysis</span>
                </div>
                <p className="text-slate-100 text-base leading-relaxed whitespace-pre-line">
                  {queryResult.answer}
                </p>
              </div>
            )}

            {/* Collapsible SQL Inspector */}
            {queryResult.sql && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
                <button
                  type="button"
                  onClick={() => setShowSql(!showSql)}
                  className="w-full flex items-center justify-between px-6 py-3.5 bg-slate-950/70 hover:bg-slate-950 transition-colors text-xs font-semibold text-slate-300 cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-emerald-400" />
                    <span>Generated PostgreSQL Query</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-slate-500 font-normal">
                      {showSql ? 'Hide SQL' : 'View SQL'}
                    </span>
                    {showSql ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </button>

                {showSql && (
                  <div className="p-4 bg-slate-950 border-t border-slate-800 relative">
                    <button
                      onClick={copySqlToClipboard}
                      className="absolute top-4 right-4 flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                    >
                      {sqlCopied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy SQL</span>
                        </>
                      )}
                    </button>
                    <pre className="text-xs font-mono text-emerald-400 overflow-x-auto p-2 pr-24 whitespace-pre-wrap">
                      {queryResult.sql}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Results Chart Visualization */}
            {queryResult.chart_suggestion &&
              queryResult.chart_suggestion.type !== 'none' &&
              queryResult.chart_suggestion.type !== 'table' && (
                <ResultsChart
                  data={queryResult.data}
                  suggestion={queryResult.chart_suggestion}
                />
              )}

            {/* Results Table */}
            {queryResult.data && queryResult.data.length > 0 && (
              <ResultsTable
                columns={queryResult.columns}
                data={queryResult.data}
              />
            )}
          </div>
        )}
      </div>
    </main>
  );
}
