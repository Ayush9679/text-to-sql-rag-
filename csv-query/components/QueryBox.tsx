'use client';

import React, { useState } from 'react';
import { Send, Sparkles, Loader2 } from 'lucide-react';

interface QueryBoxProps {
  isLoading: boolean;
  disabled: boolean;
  onSubmit: (question: string) => void;
  sampleColumns?: string[];
}

export const QueryBox: React.FC<QueryBoxProps> = ({
  isLoading,
  disabled,
  onSubmit,
  sampleColumns = [],
}) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!question.trim() || isLoading || disabled) return;
    onSubmit(question.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const suggestions = [
    'How many total records are there?',
    sampleColumns.length > 0
      ? `What are the top 5 values by ${sampleColumns[0]}?`
      : 'Show the highest values by category',
    'Summarize the distribution of the data',
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          Ask a Question
        </h2>
        <span className="text-xs text-slate-500">
          Press <kbd className="bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded text-[10px]">Enter</kbd> to submit
        </span>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div className="relative">
          <textarea
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isLoading}
            placeholder={
              disabled
                ? 'Please upload or select a dataset first...'
                : 'Ask anything in plain English, e.g. "What is total revenue by state?"'
            }
            className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-xl p-3.5 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none placeholder:text-slate-600 disabled:opacity-50"
          />
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          {/* Suggestion Chips */}
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map((sug, i) => (
              <button
                type="button"
                key={i}
                disabled={disabled || isLoading}
                onClick={() => {
                  setQuestion(sug);
                  onSubmit(sug);
                }}
                className="text-xs bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-full transition-colors disabled:opacity-40"
              >
                {sug}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={disabled || isLoading || !question.trim()}
            className="self-end sm:self-auto flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-all duration-150 shadow-md shadow-indigo-600/20 cursor-pointer disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <span>Run Query</span>
                <Send className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
