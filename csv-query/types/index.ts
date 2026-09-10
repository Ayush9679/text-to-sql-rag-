export type ColumnType = 'number' | 'date' | 'text';

export interface ColumnDefinition {
  name: string;
  type: ColumnType;
}

export interface Dataset {
  id: string;
  name: string;
  columns: ColumnDefinition[];
  row_count: number;
  blob_url?: string | null;
  created_at: string;
}

export type ChartType = 'bar' | 'line' | 'pie' | 'table' | 'none';

export interface ChartSuggestion {
  type: ChartType;
  x?: string | null;
  y?: string | null;
}

export interface QueryResponse {
  answer: string | null;
  sql: string | null;
  data: Record<string, unknown>[];
  columns: string[];
  chart_suggestion: ChartSuggestion;
  needs_clarification: boolean;
  clarification_question: string | null;
  error?: string | null;
}

export interface UploadResponse {
  datasetId: string;
  name: string;
  columns: ColumnDefinition[];
  rowCount: number;
}
