import React, { useCallback, useEffect, useState } from 'react';
import { QueryMessage, ClarificationOption } from '../types';
import { ChatContainer } from '../components/chat/ChatContainer';
import { QueryInput } from '../components/chat/QueryInput';
import { ExecutionStatusBar } from '../components/query/ExecutionStatusBar';
import { DatasetSummary, DatasetUploadPanel } from '../components/dataset/DatasetUploadPanel';
import { BackendQueryResponse, submitQuery } from '../services/queryApi';

export const WorkspacePage: React.FC = () => {
  const [messages, setMessages] = useState<QueryMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(true);
  const [datasetsError, setDatasetsError] = useState<string | null>(null);

  const loadDatasets = useCallback(async () => {
    setIsLoadingDatasets(true);
    setDatasetsError(null);
    try {
      const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
      const response = await fetch(`${apiBaseUrl}/datasets`, { credentials: 'include' });
      const body: unknown = await response.json().catch(() => null);
      if (!response.ok) throw new Error('Could not load workspace datasets.');
      const values = Array.isArray(body) ? body : body && typeof body === 'object' && 'datasets' in body && Array.isArray(body.datasets) ? body.datasets : [];
      setDatasets(values.filter((item): item is DatasetSummary => Boolean(item && typeof item === 'object' && 'table_name' in item && typeof item.table_name === 'string')));
    } catch (error) { setDatasetsError(error instanceof Error ? error.message : 'Could not load workspace datasets.'); }
    finally { setIsLoadingDatasets(false); }
  }, []);

  useEffect(() => { void loadDatasets(); }, [loadDatasets]);

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
      return { id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'error', errorMessage: response.explanation || 'The query could not be completed.', generatedSql: response.sql || undefined };
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
      const response = await submitQuery(state
        ? { query: queryText, clarification_state: state, clarification_answer: queryText }
        : { query: queryText });
      setMessages((prev) => [...prev, toAssistantMessage(response)]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to reach the query service.';
      setMessages((prev) => [...prev, {
        id: `msg-${Date.now()}`, sender: 'assistant', timestamp: new Date().toISOString(), status: 'error', errorMessage: message,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClarificationSelect = (option: ClarificationOption) => {
    if (option.clarificationState) handleSendQuery(option.label, option.clarificationState);
  };

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto">
      <ExecutionStatusBar />

      <div className="flex-1 overflow-y-auto py-6 px-2 sm:px-4">
        <DatasetUploadPanel datasets={datasets} isLoadingDatasets={isLoadingDatasets} datasetsError={datasetsError} onUploadComplete={loadDatasets} />
        <ChatContainer
          messages={messages}
          isLoading={isLoading}
          onSelectSuggestion={handleSendQuery}
          onClarificationSelect={handleClarificationSelect}
          onExecuteSql={(sql) => console.log('Run SQL:', sql)}
        />
      </div>

      <div className="pt-2 pb-4 sticky bottom-0 bg-gradient-to-t from-[#090D16] via-[#090D16] to-transparent">
        <QueryInput onSend={handleSendQuery} isLoading={isLoading} />
      </div>
    </div>
  );
};
