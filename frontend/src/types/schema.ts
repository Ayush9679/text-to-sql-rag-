export interface ColumnDefinition {
  name: string;
  type: string;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  foreignKeyTarget?: {
    table: string;
    column: string;
  };
  isNullable: boolean;
  description?: string;
  sampleValues?: (string | number)[];
}

export interface TableDefinition {
  name: string;
  schema: string;
  description: string;
  rowCount: number;
  columns: ColumnDefinition[];
  indexes?: string[];
}

export interface DatabaseSchema {
  name: string;
  dialect: 'postgresql' | 'mysql' | 'snowflake' | 'bigquery' | 'sqlite';
  version: string;
  tables: TableDefinition[];
  relationships: SchemaRelationship[];
}

export interface SchemaRelationship {
  id: string;
  sourceTable: string;
  sourceColumn: string;
  targetTable: string;
  targetColumn: string;
  type: 'one-to-one' | 'one-to-many' | 'many-to-one' | 'many-to-many';
}
