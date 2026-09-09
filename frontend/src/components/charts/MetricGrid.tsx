import React from 'react';
import { Database, TrendingUp, Layers, MessageSquareCode } from 'lucide-react';
import { KpiCard } from './KpiCard';
import { EmptyState } from '../ui/EmptyState';

export interface DashboardMetrics {
  tables_count: number;
  total_rows: number;
  total_columns: number;
  recent_queries: number;
}

export interface MetricGridProps {
  data?: DashboardMetrics | null;
  isLoading?: boolean;
}

const SkeletonCard: React.FC = () => (
  <div className="p-4 bg-slate-900/80 rounded-2xl border border-slate-800 animate-pulse space-y-3">
    <div className="flex items-start justify-between">
      <div className="space-y-2">
        <div className="h-3 w-20 bg-slate-800 rounded" />
        <div className="h-7 w-28 bg-slate-800 rounded" />
      </div>
      <div className="p-2.5 rounded-xl bg-slate-800 w-10 h-10" />
    </div>
    <div className="pt-2.5 border-t border-slate-800/80">
      <div className="h-3 w-32 bg-slate-800 rounded" />
    </div>
  </div>
);

export const MetricGrid: React.FC<MetricGridProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!data || (data.tables_count === 0 && data.total_rows === 0)) {
    return (
      <EmptyState
        icon={<Database className="w-6 h-6" />}
        title="No datasets uploaded yet"
        description="Upload a CSV file in the workspace to see real-time KPIs and analytics here."
        compact
      />
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <KpiCard
        title="Datasets"
        value={data.tables_count.toLocaleString()}
        subtitle="Uploaded tables"
        icon={<Database className="w-5 h-5" />}
        variant="indigo"
      />
      <KpiCard
        title="Total Rows"
        value={data.total_rows.toLocaleString()}
        subtitle="Across all tables"
        icon={<TrendingUp className="w-5 h-5" />}
        variant="emerald"
      />
      <KpiCard
        title="Total Columns"
        value={data.total_columns.toLocaleString()}
        subtitle="Schema attributes"
        icon={<Layers className="w-5 h-5" />}
        variant="amber"
      />
      <KpiCard
        title="Queries Run"
        value={data.recent_queries.toLocaleString()}
        subtitle="This session"
        icon={<MessageSquareCode className="w-5 h-5" />}
        variant="cyan"
      />
    </div>
  );
};
