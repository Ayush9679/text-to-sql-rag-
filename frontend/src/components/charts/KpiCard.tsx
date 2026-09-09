import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { Card } from '../ui/Card';
import { cn } from '../../utils/cn';

export interface KpiCardProps {
  title: string;
  value: string | number;
  changePercent?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  subtitle?: string;
  variant?: 'indigo' | 'emerald' | 'cyan' | 'amber';
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  changePercent,
  changeLabel = 'vs previous period',
  icon,
  subtitle,
  variant = 'indigo',
}) => {
  const borderColors = {
    indigo: 'border-slate-800 hover:border-indigo-500/30',
    emerald: 'border-slate-800 hover:border-emerald-500/30',
    cyan: 'border-slate-800 hover:border-cyan-500/30',
    amber: 'border-slate-800 hover:border-amber-500/30',
  };

  const iconColors = {
    indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  };

  return (
    <Card className={cn('p-4 transition-all duration-200 bg-slate-900/80', borderColors[variant])}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-slate-400">{title}</p>
          <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">{value}</h3>
        </div>
        {icon && (
          <div className={cn('p-2.5 rounded-xl border', iconColors[variant])}>
            {icon}
          </div>
        )}
      </div>

      {(changePercent !== undefined || subtitle) && (
        <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs">
          {changePercent !== undefined ? (
            <div className="flex items-center space-x-1.5">
              <span
                className={cn(
                  'inline-flex items-center font-medium px-1.5 py-0.5 rounded text-[11px]',
                  changePercent > 0
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : changePercent < 0
                    ? 'bg-rose-500/10 text-rose-400'
                    : 'bg-slate-800 text-slate-400'
                )}
              >
                {changePercent > 0 ? (
                  <ArrowUpRight className="w-3 h-3 mr-0.5" />
                ) : changePercent < 0 ? (
                  <ArrowDownRight className="w-3 h-3 mr-0.5" />
                ) : (
                  <Minus className="w-3 h-3 mr-0.5" />
                )}
                {Math.abs(changePercent)}%
              </span>
              <span className="text-slate-500 text-[11px] truncate">{changeLabel}</span>
            </div>
          ) : (
            <span className="text-slate-500 text-[11px]">{subtitle}</span>
          )}
        </div>
      )}
    </Card>
  );
};
