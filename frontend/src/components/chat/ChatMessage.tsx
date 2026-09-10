import React, { useState } from 'react';
import { Bot, User, Clock, CheckCircle2, ChevronDown, ChevronUp, AlertCircle, Sparkles, Layers, BarChart3, Table as TableIcon } from 'lucide-react';
import { QueryMessage, ClarificationOption } from '../../types';
import { ConfidenceBadge } from '../confidence/ConfidenceBadge';
import { ConfidenceBreakdown } from '../confidence/ConfidenceBreakdown';
import { ClarificationPrompt } from '../clarification/ClarificationPrompt';
import { SqlViewer } from '../sql/SqlViewer';
import { DataTable } from '../results/DataTable';
import { formatExecutionTime, formatTimestamp } from '../../utils/formatters';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

export interface ChatMessageProps {
  message: QueryMessage;
  onClarificationSelect?: (option: ClarificationOption) => void;
  onExecuteSql?: (sql: string) => void;
  /** DataQuery AI v2: called when user clicks an alternative interpretation chip. */
  onRunAlternative?: (sql: string, tableName: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onClarificationSelect,
  onExecuteSql,
  onRunAlternative,
}) => {
  const [showConfidenceDetails, setShowConfidenceDetails] = useState(false);
  const [activeView, setActiveView] = useState<'table' | 'sql' | 'summary'>('table');
  const [isExplanationExpanded, setIsExplanationExpanded] = useState(true);

  if (message.sender === 'user') {
    return (
      <div className="flex items-start justify-end space-x-3 mb-6">
        <div className="max-w-2xl bg-indigo-600/20 border border-indigo-500/30 rounded-2xl rounded-tr-sm p-4 text-slate-100 shadow-md">
          <div className="flex items-center space-x-2 mb-1.5 justify-end">
            <span className="text-[11px] text-indigo-300 font-medium">You</span>
            <span className="text-[10px] text-slate-400">{formatTimestamp(message.timestamp)}</span>
          </div>
          <p className="text-sm font-medium leading-relaxed">{message.naturalQuery}</p>
        </div>
        <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white flex-shrink-0 shadow-sm mt-1">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  // Assistant AI Response Card
  return (
    <div className="flex items-start space-x-3.5 mb-8 animate-fade-in">
      <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-600 flex items-center justify-center text-white flex-shrink-0 shadow-glow-primary mt-1">
        <Bot className="w-5 h-5" />
      </div>

      <div className="flex-1 max-w-4xl space-y-4">
        {/* Header with Title and Confidence */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2.5 pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> AI Database Analyst
              </span>
              <span className="text-[11px] text-slate-500">{formatTimestamp(message.timestamp)}</span>
            </div>

            {message.confidence && (
              <div className="flex items-center space-x-2">
                <ConfidenceBadge score={message.confidence.score} />
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-slate-400 hover:text-white"
                  onClick={() => setShowConfidenceDetails(!showConfidenceDetails)}
                  aria-label="Toggle confidence breakdown"
                >
                  {showConfidenceDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </Button>
              </div>
            )}
          </div>

          {/* Confidence Breakdown dropdown */}
          {showConfidenceDetails && message.confidence && (
            <ConfidenceBreakdown confidence={message.confidence} />
          )}

          {/* Clarification State */}
          {message.status === 'clarifying' && message.clarification && (
            <ClarificationPrompt
              request={message.clarification}
              onConfirmSelection={onClarificationSelect}
            />
          )}

          {/* Natural Language Answer */}
          {message.naturalAnswer && (
            <div className="text-sm text-slate-200 leading-relaxed font-normal bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/80">
              {message.naturalAnswer}
            </div>
          )}

          {/* DataQuery AI v2: Alternative interpretation chips */}
          {message.alternatives && message.alternatives.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="text-[11px] text-slate-500 self-center font-medium uppercase tracking-wider">Try instead:</span>
              {message.alternatives.map((alt, i) => (
                <button
                  key={i}
                  id={`alt-chip-${message.id}-${i}`}
                  onClick={() => onRunAlternative?.(alt.sql, message.dataQueryTableName ?? '')}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 hover:bg-indigo-500/20 hover:border-indigo-400/40 hover:text-indigo-200 transition-all duration-150 cursor-pointer"
                  title={alt.sql}
                >
                  {alt.label} →
                </button>
              ))}
            </div>
          )}

          {/* Query Explanation Section */}
          {message.queryExplanation && (
            <div className="space-y-1.5">
              <button
                type="button"
                onClick={() => setIsExplanationExpanded(!isExplanationExpanded)}
                className="flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-slate-200"
              >
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                <span>Query Strategy & Explanation</span>
                {isExplanationExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>

              {isExplanationExpanded && (
                <p className="text-xs text-slate-400 bg-slate-950/30 p-3 rounded-lg border border-slate-800/60 leading-relaxed">
                  {message.queryExplanation}
                </p>
              )}
            </div>
          )}

          {/* Error Message if Error Status */}
          {message.status === 'error' && message.errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start space-x-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block mb-0.5">Execution Failed</span>
                <span>{message.errorMessage}</span>
              </div>
            </div>
          )}

          {/* View Switcher Tabs (Results vs SQL vs Summary) */}
          {(message.generatedSql || message.results) && (
            <div className="pt-2">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
                  {message.results && (
                    <button
                      onClick={() => setActiveView('table')}
                      className={cn(
                        'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                        activeView === 'table'
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200'
                      )}
                    >
                      <TableIcon className="w-3.5 h-3.5" />
                      <span>Data Table ({message.results.totalRows})</span>
                    </button>
                  )}

                  {message.generatedSql && (
                    <button
                      onClick={() => setActiveView('sql')}
                      className={cn(
                        'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                        activeView === 'sql'
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200'
                      )}
                    >
                      <Layers className="w-3.5 h-3.5" />
                      <span>Generated SQL</span>
                    </button>
                  )}

                  {message.resultSummary && (
                    <button
                      onClick={() => setActiveView('summary')}
                      className={cn(
                        'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                        activeView === 'summary'
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200'
                      )}
                    >
                      <BarChart3 className="w-3.5 h-3.5" />
                      <span>Summary</span>
                    </button>
                  )}
                </div>

                {/* Execution Metadata Pill */}
                {message.executionMeta && (
                  <div className="flex items-center space-x-3 text-[11px] font-mono text-slate-400 hidden sm:flex">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {formatExecutionTime(message.executionMeta.executionTimeMs)}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1 text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" />
                      {message.executionMeta.rowsAffected} rows
                    </span>
                  </div>
                )}
              </div>

              {/* View Content Panels */}
              {activeView === 'table' && message.results && (
                <DataTable data={message.results} />
              )}

              {activeView === 'sql' && message.generatedSql && (
                <SqlViewer
                  sql={message.generatedSql}
                  dialect={message.executionMeta?.dialect || 'PostgreSQL'}
                  onExecute={onExecuteSql ? () => onExecuteSql(message.generatedSql!) : undefined}
                />
              )}

              {activeView === 'summary' && message.resultSummary && (
                <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  <h5 className="font-semibold text-slate-200 mb-1.5 uppercase tracking-wider text-[11px]">
                    Result Key Insights
                  </h5>
                  <p>{message.resultSummary}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
