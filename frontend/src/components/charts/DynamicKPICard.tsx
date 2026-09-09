import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus, Database } from 'lucide-react';
import { Card } from '../ui/Card';
import { cn } from '../../utils/cn';
import { DynamicKPI } from '../../services/dashboardApi';

interface DynamicKPICardProps {
  kpi: DynamicKPI;
  variant?: 'indigo' | 'emerald' | 'cyan' | 'amber' | 'violet' | 'rose';
}

const variantColors = {
  indigo: { border: 'border-slate-800 hover:border-indigo-500/30', icon: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
  emerald: { border: 'border-slate-800 hover:border-emerald-500/30', icon: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  cyan: { border: 'border-slate-800 hover:border-cyan-500/30', icon: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  amber: { border: 'border-slate-800 hover:border-amber-500/30', icon: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  violet: { border: 'border-slate-800 hover:border-violet-500/30', icon: 'bg-violet-500/10 text-violet-400 border-violet-500/20' },
  rose: { border: 'border-slate-800 hover:border-rose-500/30', icon: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
};

const VARIANTS: Array<DynamicKPICardProps['variant']> = ['indigo', 'emerald', 'cyan', 'amber', 'violet', 'rose'];

export const DynamicKPICard: React.FC<DynamicKPICardProps> = ({ kpi, variant }) => {
  const colors = variantColors[variant || 'indigo'];

  return (
    <Card className={cn('p-4 transition-all duration-200 bg-slate-900/80', colors.border)}>
      <div className="flex items-start justify-between">
        <div className="space-y-1 min-w-0">
          <p className="text-xs font-medium text-slate-400 truncate">{kpi.label}</p>
          <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight truncate">{kpi.formatted_value}</h3>
        </div>
        <div className={cn('p-2.5 rounded-xl border flex-shrink-0', colors.icon)}>
          <Database className="w-5 h-5" />
        </div>
      </div>

      {(kpi.comparison !== undefined) && (
        <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-1.5">
            <span
              className={cn(
                'inline-flex items-center font-medium px-1.5 py-0.5 rounded text-[11px]',
                kpi.comparison.change_percent > 0
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : kpi.comparison.change_percent < 0
                  ? 'bg-rose-500/10 text-rose-400'
                  : 'bg-slate-800 text-slate-400'
              )}
            >
              {kpi.comparison.change_percent > 0 ? (
                <ArrowUpRight className="w-3 h-3 mr-0.5" />
              ) : kpi.comparison.change_percent < 0 ? (
                <ArrowDownRight className="w-3 h-3 mr-0.5" />
              ) : (
                <Minus className="w-3 h-3 mr-0.5" />
              )}
              {Math.abs(kpi.comparison.change_percent)}%
            </span>
            <span className="text-slate-500 text-[11px] truncate">vs previous period</span>
          </div>
        </div>
      )}
    </Card>
  );
};

interface KPIGridProps {
  kpis: DynamicKPI[];
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

export const DynamicKPIGrid: React.FC<KPIGridProps> = ({ kpis, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (kpis.length === 0) {
    return (
      <div className="p-8 bg-slate-900/60 rounded-2xl border border-slate-800 text-center">
        <Database className="w-10 h-10 mx-auto text-slate-600 mb-3" />
        <h4 className="text-sm font-semibold text-white">No KPIs Available</h4>
        <p className="text-xs text-slate-400 mt-1">
          Upload data and run queries to discover meaningful metrics.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi, idx) => (
        <DynamicKPICard key={kpi.id} kpi={kpi} variant={VARIANTS[idx % VARIANTS.length]} />
      ))}
    </div>
  );
};