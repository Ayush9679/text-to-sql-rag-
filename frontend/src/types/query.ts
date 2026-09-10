export type QueryStatus = 'idle' | 'generating' | 'clarifying' | 'executing' | 'completed' | 'error';

export interface ConfidenceFactors {
  schemaAlignment: number;
  intentClarity: number;
  syntaxValidity: number;
  ragGrounding: number;
}

export interface ConfidenceData {
  score: number;
  tier: 'high' | 'medium' | 'low';
  factors: ConfidenceFactors;
  explanation: string;
}

export interface ClarificationOption {
  id: string;
  label: string;
  description: string;
  sqlHint?: string;
  clarificationState?: Record<string, unknown>;
}

export interface ClarificationRequest {
  id: string;
  question: string;
  ambiguityType: 'metric_definition' | 'time_granularity' | 'entity_filter' | 'aggregation';
  options: ClarificationOption[];
  selectedOptionId?: string;
}

export interface QueryExecutionMeta {
  executionTimeMs: number;
  rowsAffected: number;
  cached: boolean;
  bytesScanned?: string;
  dialect: string;
}

export interface QueryResultData {
  columns: string[];
  rows: Record<string, any>[];
  totalRows: number;
}

export interface AlternativeQuery {
  label: string;
  sql: string;
}

export interface QueryMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  naturalQuery?: string;
  naturalAnswer?: string;
  generatedSql?: string;
  queryExplanation?: string;
  resultSummary?: string;
  status: QueryStatus;
  confidence?: ConfidenceData;
  clarification?: ClarificationRequest;
  results?: QueryResultData;
  executionMeta?: QueryExecutionMeta;
  errorMessage?: string;
  /** Pre-generated alternate SQL interpretations (v2 no-dead-end contract). */
  alternatives?: AlternativeQuery[];
  /** DataQuery AI v2: table name the query ran against (needed for execute-sql). */
  dataQueryTableName?: string;
}


export interface QueryHistoryItem {
  id: string;
  naturalQuery: string;
  generatedSql: string;
  status: 'success' | 'failed' | 'clarified';
  timestamp: string;
  confidenceScore: number;
  executionTimeMs: number;
  category: string;
  rowCount: number;
}
