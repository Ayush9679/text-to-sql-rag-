import React, { useCallback, useEffect, useState } from 'react';
import { QueryMessage, ClarificationOption } from '../types';
import { ChatContainer } from '../components/chat/ChatContainer';
import { QueryInput } from '../components/chat/QueryInput';
import { ExecutionStatusBar } from '../components/query/ExecutionStatusBar';
import { DatasetSummary, DatasetUploadPanel } from '../components/dataset/DatasetUploadPanel';
import { BackendQueryResponse, submitQuery } from '../services/queryApi';
import { submitDataQuery, executeAlternativeSql, DataQueryResponse } from '../services/dashboardApi';

// ── DataQuery mode indicator badge ───────────────────────────────────────────

const DataQueryBadge: React.FC<{
  active: boolean;
  tableName: string | null;
  tables: DatasetSummary[];
  onToggle: () => void;
  onTableChange: (t: string) => void;
}> = ({ active, tableName, tables, onToggle, onTableChange }) => (
  <div className="flex items-center gap-2 px-3 py-1.5 mb-2 rounded-xl border border-slate-700 bg-slate-900/70 text-xs select-none">
    <button
      id="dataquery-mode-toggle"
      onClick={onToggle}
      className={`flex items-center gap-1.5 px-2 py-0.5 rounded-lg font-medium transition-all duration-200 ${
        active
          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_8px_rgba(34,211,238,0.15)]'
          : 'text-slate-400 hover:text-slate-200 border border-transparent hover:border-slate-600'
      }`}
      title={active ? 'Switch to standard Text-to-SQL mode' : 'Switch to DataQuery AI mode'}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${active ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`} />
      DataQuery AI
    </button>

    {active && tables.length > 0 && (
      <>
        <span className="text-slate-600">·</span>
        <span className="text-slate-500">table:</span>
        <select
          id="dataquery-table-select"
          value={tableName ?? ''}
          onChange={(e) => onTableChange(e.target.value)}
          className="bg-transparent text-cyan-300 border-none outline-none cursor-pointer text-xs"
        >
          {tables.map((t) => (
            <option key={t.table_name} value={t.table_name} className="bg-slate-900 text-slate-200">
              {t.table_name}
            </option>
          ))}
        </select>
      </>
    )}

    <span className="text-slate-600 ml-auto">
      {active ? 'AI analyst · SQL-grounded' : 'Standard Text-to-SQL'}
    </span>
  </div>
);

// ── Main WorkspacePage ────────────────────────────────────────────────────────

export const WorkspacePage: React.FC = () => {
  const [messages, setMessages] = useState<QueryMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(true);
  const [datasetsError, setDatasetsError] = useState<string | null>(null);

  // DataQuery mode state
  const [dataQueryMode, setDataQueryMode] = useState(false);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  const loadDatasets = useCallback(async () => {
    setIsLoadingDatasets(true);
    setDatasetsError(null);
    try {
      const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
      const response = await fetch(`${apiBaseUrl}/datasets`, { credentials: 'include' });
      const body: unknown = await response.json().catch(() => null);
      if (!response.ok) throw new Error('Could not load workspace datasets.');
      const values = Array.isArray(body)
        ? body
        : body && typeof body === 'object' && 'datasets' in body && Array.isArray(body.datasets)
        ? body.datasets
        : [];
      const parsed = values.filter(
        (item): item is DatasetSummary =>
          Boolean(item && typeof item === 'object' && 'table_name' in item && typeof item.table_name === 'string'),
      );
      setDatasets(parsed);
      // Auto-select first table for DataQuery mode if none chosen yet
      setSelectedTable((prev) => (prev ? prev : parsed.length > 0 ? parsed[0].table_name : null));
    } catch (error) {
      setDatasetsError(error instanceof Error ? error.message : 'Could not load workspace datasets.');
    } finally {
      setIsLoadingDatasets(false);
    }
  }, []);

  useEffect(() => { void loadDatasets(); }, [loadDatasets]);

  // ── Map standard backend response → QueryMessage ─────────────────────────
  const toAssistantMessage = (response: BackendQueryResponse): QueryMessage => {
    const metadata = response.metadata || {};
    if (response.status === 'clarification_required' && response.clarification) {
      return {
        id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'clarifying',
        queryExplanation: response.explanation || undefined,
        clarification: {
          id: `clarify-${Date.now()}`,
          question: response.clarification.question,
          ambiguityType: 'metric_definition',
          options: response.clarification.options.map((label, index) => ({
            id: `option-${index}`,
            label,
            description: `Use ${label} to answer this question.`,
            clarificationState: response.clarification_state || undefined,
          })),
        },
      };
    }
    if (response.status === 'failed') {
      return {
        id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'error',
        errorMessage: response.explanation || 'The query could not be completed.',
        generatedSql: response.sql || undefined,
      };
    }
    return {
      id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'completed',
      naturalAnswer: response.explanation || `${response.row_count} row${response.row_count === 1 ? '' : 's'} returned.`,
      generatedSql: response.sql || undefined,
      results: { columns: response.columns, rows: response.rows, totalRows: response.row_count },
      executionMeta: {
        executionTimeMs: typeof metadata.execution_time_ms === 'number' ? metadata.execution_time_ms : 0,
        rowsAffected: response.row_count, cached: false, dialect: 'PostgreSQL',
      },
    };
  };

  // ── Map DataQuery response → QueryMessage ────────────────────────────────
  const toDataQueryMessage = (response: DataQueryResponse): QueryMessage => {
    if (response.needs_clarification && response.clarification_question) {
      return {
        id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'clarifying',
        queryExplanation: response.clarification_question,
        clarification: {
          id: `clarify-${Date.now()}`,
          question: response.clarification_question,
          ambiguityType: 'metric_definition',
          options: [],
        },
      };
    }

    if (response.error && !response.answer) {
      return {
        id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'error',
        errorMessage: response.error,
        generatedSql: response.sql || undefined,
      };
    }

    const assumptionsNote =
      response.assumptions?.length ? `\n\n_Assumptions: ${response.assumptions.join('; ')}_` : '';
    const naturalAnswer =
      (response.answer || `${response.row_count_returned} row(s) returned.`) + assumptionsNote;

    return {
      id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'completed',
      naturalAnswer,
      generatedSql: response.sql || undefined,
      results:
        response.data.length > 0
          ? {
              columns: response.columns,
              rows: response.data as Record<string, unknown>[],
              totalRows: response.row_count_returned,
            }
          : undefined,
      executionMeta: {
        executionTimeMs: 0,
        rowsAffected: response.row_count_returned,
        cached: false,
        dialect: 'PostgreSQL',
      },
      alternatives: response.alternatives?.length ? response.alternatives : undefined,
      dataQueryTableName: response.table_name || undefined,
    };
  };
  
  // ── Run an alternative SQL interpretation — no LLM call ──────────────────
  const handleRunAlternative = async (sql: string, tableName: string | undefined) => {
    if (!tableName) return;
    setIsLoading(true);
    try {
      const result = await executeAlternativeSql(sql, tableName);
      const altMsg: QueryMessage = {
        id: `msg-${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        status: 'completed',
        naturalAnswer: `${result.row_count} row(s) returned (alternative view).`,
        generatedSql: sql,
        results:
          result.data.length > 0
            ? { columns: result.columns, rows: result.data as Record<string, unknown>[], totalRows: result.row_count }
            : undefined,
        executionMeta: { executionTimeMs: 0, rowsAffected: result.row_count, cached: false, dialect: 'PostgreSQL' },
      };
      setMessages((prev) => [...prev, altMsg]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Alternative query failed.';
      setMessages((prev) => [
        ...prev,
        { id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'error', errorMessage: message },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // ── Send query — dispatches to standard or DataQuery pipeline ────────────
  const handleSendQuery = async (queryText: string, state?: Record<string, unknown> | null) => {
    const userMsg: QueryMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toISOString(),
      naturalQuery: queryText,
      status: 'completed',
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    try {
      if (dataQueryMode) {
        const response = await submitDataQuery({
          query: queryText,
          ...(selectedTable ? { table_name: selectedTable } : {}),
        });
        setMessages((prev) => [...prev, toDataQueryMessage(response)]);
      } else {
        const response = await submitQuery(
          state
            ? { query: queryText, clarification_state: state, clarification_answer: queryText }
            : { query: queryText },
        );
        setMessages((prev) => [...prev, toAssistantMessage(response)]);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to reach the query service.';
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now()}`,
          sender: 'assistant',
          timestamp: new Date().toISOString(),
          status: 'error',
          errorMessage: message,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClarificationSelect = (option: ClarificationOption) => {
    if (option.clarificationState) handleSendQuery(option.label, option.clarificationState);
  };

  const handleToggleDataQuery = () => {
    setDataQueryMode((prev) => {
      const next = !prev;
      // Ensure a table is selected when enabling DataQuery mode
      if (next && !selectedTable && datasets.length > 0) {
        setSelectedTable(datasets[0].table_name);
      }
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto">
      <ExecutionStatusBar />

      <div className="flex-1 overflow-y-auto py-6 px-2 sm:px-4">
        <DatasetUploadPanel
          datasets={datasets}
          isLoadingDatasets={isLoadingDatasets}
          datasetsError={datasetsError}
          onUploadComplete={loadDatasets}
        />
        <ChatContainer
          messages={messages}
          isLoading={isLoading}
          onSelectSuggestion={handleSendQuery}
          onClarificationSelect={handleClarificationSelect}
          onExecuteSql={(sql) => console.log('Run SQL:', sql)}
          onRunAlternative={handleRunAlternative}
        />
      </div>

      <div className="pt-2 pb-4 sticky bottom-0 bg-gradient-to-t from-[#090D16] via-[#090D16] to-transparent">
        <DataQueryBadge
          active={dataQueryMode}
          tableName={selectedTable}
          tables={datasets}
          onToggle={handleToggleDataQuery}
          onTableChange={setSelectedTable}
        />
        <QueryInput onSend={handleSendQuery} isLoading={isLoading} />
      </div>
    </div>
  );
};
