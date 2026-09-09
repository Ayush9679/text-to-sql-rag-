import { QueryMessage, DatabaseSchema, KnowledgeDocument, QueryHistoryItem } from '../types';

export interface GenerateSqlQueryRequest {
  naturalPrompt: string;
  dialect?: string;
  temperature?: number;
}

export interface GenerateSqlQueryResponse {
  queryMessage: QueryMessage;
}

export interface IntrospectSchemaResponse {
  schema: DatabaseSchema;
}

export interface KnowledgeSearchResponse {
  documents: KnowledgeDocument[];
}

export interface HistoryListResponse {
  items: QueryHistoryItem[];
}
