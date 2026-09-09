import React, { useEffect, useState } from 'react';
import { DynamicKPIGrid } from './DynamicKPICard';
import { BarChartVisual, BarChartDataPoint } from './BarChartVisual';
import { LineChartVisual, LineChartDataPoint } from './LineChartVisual';
import { DonutChartVisual, DonutSegment } from './DonutChartVisual';
import { EmptyState } from '../ui/EmptyState';
import {
  fetchDashboardKPIs,
  fetchDashboardTrends,
  fetchDashboardBreakdowns,
  fetchQueryVolume,
  DynamicKPI,
  TrendPoint,
  BreakdownPoint,
  QueryVolumePoint,
} from '../../services/dashboardApi';

export const AnalyticsDashboard: React.FC = () => {
  const [kpis, setKpis] = useState<DynamicKPI[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [breakdowns, setBreakdowns] = useState<BreakdownPoint[]>([]);
  const [queryVolume, setQueryVolume] = useState<QueryVolumePoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [kpiData, trendData, breakdownData, volumeData] = await Promise.all([
        fetchDashboardKPIs(),
        fetchDashboardTrends('month'),
        fetchDashboardBreakdowns(),
        fetchQueryVolume(),
      ]);

      setKpis(kpiData);
      setTrends(trendData);
      setBreakdowns(breakdownData);
      setQueryVolume(volumeData);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Convert API data to chart formats
  const barChartData: BarChartDataPoint[] = trends.map((t) => ({
    label: t.period,
    value: t.value,
    formattedValue: t.formatted_value,
  }));

  const lineChartData: LineChartDataPoint[] = queryVolume.map((q) => ({
    label: q.period,
    value: q.value,
  }));

  const donutData: DonutSegment[] = breakdowns.map((b, idx) => ({
    label: b.label,
    value: b.value,
    formattedValue: b.formatted_value,
    percentage: b.percentage,
    color: ['#6366F1', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#EC4899', '#8B5CF6', '#06D6A0'][idx % 8],
  }));

  if (isLoading) {
    return (
      <div className="space-y-6">
        <DynamicKPIGrid kpis={[]} isLoading={true} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <BarChartVisual title="Loading..." data={[]} />
          </div>
          <div>
            <DonutChartVisual title="Loading..." data={[]} />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <LineChartVisual title="Loading..." data={[]} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <EmptyState
          icon={<div className="w-12 h-12 rounded-xl bg-rose-500/10 flex items-center justify-center"><svg className="w-6 h-6 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg></div>}
          title="Unable to Load Analytics"
          description={error}
          action={<button onClick={loadDashboardData} className="text-cyan-400 hover:text-cyan-300 font-mono text-sm">Retry</button>}
        />
      </div>
    );
  }

  // Determine if we have any meaningful data
  const hasData = kpis.length > 0 || trends.length > 0 || breakdowns.length > 0 || queryVolume.length > 0;

  if (!hasData) {
    return (
      <div className="space-y-6">
        <EmptyState
          icon={<div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center"><svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg></div>}
          title="No Analytics Data Available"
          description="Upload datasets and run queries to populate the dashboard with real insights from your data."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Last Updated Indicator */}
      {lastUpdated && (
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Dashboard updated {lastUpdated.toLocaleTimeString()}</span>
          <button
            onClick={loadDashboardData}
            className="text-cyan-400 hover:text-cyan-300 font-mono flex items-center space-x-1"
            disabled={isLoading}
          >
            <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
            <span>Refresh</span>
          </button>
        </div>
      )}

      {/* KPI Grid */}
      <DynamicKPIGrid kpis={kpis} isLoading={false} />

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <BarChartVisual
            title={trends.length > 0 ? 'Monthly Trend' : 'Trend'}
            subtitle={trends.length > 0 ? `Data points: ${trends.length}` : 'No time-series data available'}
            data={barChartData}
          />
        </div>
        <div>
          <DonutChartVisual
            title={breakdowns.length > 0 ? 'Category Breakdown' : 'Breakdown'}
            subtitle={breakdowns.length > 0 ? `Top ${breakdowns.length} categories` : 'No categorical data available'}
            data={donutData}
          />
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6">
        <LineChartVisual
          title={queryVolume.length > 0 ? 'Query Execution Volume' : 'Query Volume'}
          subtitle={queryVolume.length > 0 ? `Last ${queryVolume.length} periods` : 'No query history available'}
          data={lineChartData}
        />
      </div>
    </div>
  );
};