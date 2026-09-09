import React, { useState } from 'react';
import { Search, RefreshCw, Layers } from 'lucide-react';
import { DatabaseSchema } from '../../types';
import { DatabaseSidebar } from './DatabaseSidebar';
import { TableCard } from './TableCard';
import { RelationshipGraph } from './RelationshipGraph';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

export interface SchemaExplorerProps {
  schema: DatabaseSchema;
}

export const SchemaExplorer: React.FC<SchemaExplorerProps> = ({ schema }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTable, setSelectedTable] = useState<string | undefined>(schema.tables[0]?.name);

  const filteredTables = schema.tables.filter((t) =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.columns.some((c) => c.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header Search & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" /> Database Schema Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Explore live tables, foreign key graphs, data types, and primary key hierarchies.
          </p>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <Input
            placeholder="Search tables or columns..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Search className="w-3.5 h-3.5" />}
            className="w-full sm:w-64 h-9 text-xs"
          />
          <Button variant="outline" size="sm" className="h-9 px-3 text-xs flex-shrink-0">
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Introspect
          </Button>
        </div>
      </div>

      {/* Main Layout */}
      <div className="flex flex-col md:flex-row gap-6">
        <DatabaseSidebar
          schema={schema}
          selectedTableName={selectedTable}
          onSelectTable={setSelectedTable}
        />

        <div className="flex-1 space-y-6">
          <RelationshipGraph relationships={schema.relationships} />

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Database Tables ({filteredTables.length})
              </h3>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {filteredTables.map((table) => (
                <TableCard
                  key={table.name}
                  table={table}
                  isSelected={selectedTable === table.name}
                  onSelect={() => setSelectedTable(table.name)}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
