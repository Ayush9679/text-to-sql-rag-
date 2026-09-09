export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  sslMode: 'require' | 'prefer' | 'disable';
  maxConnections: number;
  timeoutSeconds: number;
  readOnly: boolean;
}

export interface AiModelConfig {
  provider: 'groq' | 'anthropic' | 'openai' | 'custom';
  modelName: string;
  temperature: number;
  maxTokens: number;
  enableThinking: boolean;
  systemPromptPreset: 'strict_sql' | 'conversational_analyst' | 'data_engineer';
}

export interface QueryPreferences {
  defaultLimit: number;
  timeoutMs: number;
  requireClarificationOnLowConfidence: boolean;
  confidenceThreshold: number;
  autoFormatSql: boolean;
  enableSafetyGuardrails: boolean;
  blockDestructiveQueries: boolean;
}

export interface SecuritySettings {
  enforceReadOnlyTransactions: boolean;
  maskSensitiveColumns: boolean;
  sensitiveColumnPatterns: string[];
  auditLoggingEnabled: boolean;
}

export interface AppSettings {
  theme: 'dark' | 'light' | 'system';
  database: DatabaseConfig;
  ai: AiModelConfig;
  query: QueryPreferences;
  security: SecuritySettings;
}
