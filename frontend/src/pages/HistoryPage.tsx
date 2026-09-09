import React, { useState } from 'react';
import { History, Search, Clock, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';
import { QueryHistoryItem } from '../types';
import { ConfidenceBadge } from '../components/confidence/ConfidenceBadge';
import { formatExecutionTime, formatTimestamp } from '../utils/formatters';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';

const sampleHistory: QueryHistoryItem[] = [
  {
    id: 'hist-1',
    naturalQuery: 'Show the top 10 customers by revenue along with their order counts and cities.',
    generatedSql: 'SELECT c.customer_id, c.first_name, c.city, COUNT(o.order_id), SUM(o.total_amount) FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY 1,2,3 ORDER BY 5 DESC LIMIT 10;',
    status: 'success',
    timestamp: '2026-08-19T10:14:00Z',
    confidenceScore: 0.94,
    executionTimeMs: 148,
    category: 'Revenue Analytics',
    rowCount: 10,
  },
  {
    id: 'hist-2',
    naturalQuery: 'What were our best-selling products last quarter by units sold?',
    generatedSql: 'SELECT p.product_name, SUM(oi.quantity) as total_units FROM products p JOIN order_items oi ON p.product_id = oi.product_id GROUP BY 1 ORDER BY 2 DESC LIMIT 5;',
    status: 'success',
    timestamp: '2026-08-19T09:40:12Z',
    confidenceScore: 0.89,
    executionTimeMs: 89,
    category: 'Product Performance',
    rowCount: 5,
  },
  {
    id: 'hist-3',
    naturalQuery: 'Show monthly revenue trends across all regions for 2026.',
    generatedSql: 'SELECT DATE_TRUNC(\'month\', order_date), SUM(total_amount) FROM orders WHERE EXTRACT(year FROM order_date) = 2026 GROUP BY 1 ORDER BY 1;',
    status: 'success',
    timestamp: '2026-08-19T09:12:45Z',
    confidenceScore: 0.92,
    executionTimeMs: 215,
    category: 'Time Series',
    rowCount: 8,
  },
  {
    id: 'hist-4',
    naturalQuery: 'Show me the best customers.',
    generatedSql: '-- Pending clarification from user',
    status: 'clarified',
    timestamp: '2026-08-19T08:50:00Z',
    confidenceScore: 0.62,
    executionTimeMs: 40,
    category: 'Ambiguity Resolution',
    rowCount: 0,
  },
  {
    id: 'hist-5',
    naturalQuery: 'Delete all inactive user accounts from the customer registry.',
    generatedSql: '-- Blocked by Read-Only Safety Guardrail',
    status: 'failed',
    timestamp: '2026-08-19T08:15:22Z',
    confidenceScore: 0.20,
    executionTimeMs: 15,
    category: 'Security Guardrail',
    rowCount: 0,
  },
];

export const HistoryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filteredHistory = sampleHistory.filter((item) => {
    const matchesSearch =
      item.naturalQuery.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" /> Natural Language Query History
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit trail of translated natural queries, confidence scores, execution times, and generated SQL.
          </p>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <Input
            placeholder="Search query history..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Search className="w-3.5 h-3.5" />}
            className="w-full sm:w-64 h-9 text-xs"
          />

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter history by status"
            className="h-9 px-3 bg-slate-900 border border-slate-700/80 rounded-lg text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
          >
            <option value="all">All Status</option>
            <option value="success">Success</option>
            <option value="clarified">Clarified</option>
            <option value="failed">Blocked / Failed</option>
          </select>
        </div>
      </div>

      {/* History Items Grid */}
      <div className="space-y-3">
        {filteredHistory.map((item) => (
          <Card
            key={item.id}
            className="p-4 bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center space-x-2.5">
                {item.status === 'success' ? (
                  <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                ) : item.status === 'clarified' ? (
                  <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
                    <HelpCircle className="w-4 h-4" />
                  </div>
                ) : (
                  <div className="p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
                    <AlertCircle className="w-4 h-4" />
                  </div>
                )}
                <div>
                  <h4 className="text-sm font-semibold text-white">{item.naturalQuery}</h4>
                  <div className="flex items-center space-x-2 text-[11px] text-slate-500 mt-0.5">
                    <span>{formatTimestamp(item.timestamp)}</span>
                    <span>•</span>
                    <span className="text-indigo-400 font-medium">{item.category}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2.5 self-start sm:self-auto">
                <ConfidenceBadge score={item.confidenceScore} />
                <Badge variant="outline" size="sm" className="font-mono text-[11px]">
                  <Clock className="w-3 h-3 mr-1" />
                  {formatExecutionTime(item.executionTimeMs)}
                </Badge>
              </div>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 font-mono text-xs text-slate-300 overflow-x-auto">
              <div className="flex items-center justify-between text-slate-500 text-[10px] uppercase mb-1">
                <span>Generated Dialect Query</span>
                {item.rowCount > 0 && <span>{item.rowCount} rows returned</span>}
              </div>
              <code className="text-indigo-300/90 leading-relaxed block">{item.generatedSql}</code>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
