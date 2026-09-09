export interface KnowledgeDocument {
  id: string;
  title: string;
  category: 'business_rule' | 'schema_annotation' | 'metric_definition' | 'synonym_mapping';
  content: string;
  relevanceScore?: number;
  source: string;
  updatedAt: string;
  tags: string[];
}

export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  conditionFormula: string;
  applicableTables: string[];
  priority: 'high' | 'medium' | 'low';
}

export interface SynonymMapping {
  id: string;
  userTerm: string;
  canonicalEntity: string;
  targetType: 'table' | 'column' | 'value' | 'metric';
  context: string;
}

export interface RetrievedContextItem {
  id: string;
  docTitle: string;
  snippet: string;
  similarity: number;
  category: string;
}
