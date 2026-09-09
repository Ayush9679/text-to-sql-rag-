import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { cn } from '../../utils/cn';

export interface BarChartDataPoint {
  label: string;
  value: number;
  secondaryValue?: number;
  formattedValue?: string;
}

export interface BarChartVisualProps {
  title?: string;
  subtitle?: string;
  data?: BarChartDataPoint[];
  height?: number;
  className?: string;
}

export const BarChartVisual: React.FC<BarChartVisualProps> = ({
  title = 'Trend',
  subtitle,
  data = [],
  className,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const maxValue = Math.max(...data.map((d) => d.value), 1);

  if (data.length === 0) {
    return (
      <Card className={cn('p-5 bg-slate-900/80 border border-slate-800 flex flex-col', className)}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="text-sm font-semibold text-white">{title}</h4>
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center min-h-[180px] text-slate-500 text-sm">
          No trend data available
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn('p-5 bg-slate-900/80 border border-slate-800 flex flex-col', className)}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-semibold text-white">{title}</h4>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex items-center space-x-3 text-xs text-slate-400">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-indigo-500 inline-block" />
            <span>Value</span>
          </div>
        </div>
      </div>

      {/* Chart visualization */}
      <div className="flex-1 flex items-end justify-between gap-2 pt-6 pb-2 min-h-[180px]">
        {data.map((item, idx) => {
          const heightPercent = (item.value / maxValue) * 100;
          const isHovered = hoveredIdx === idx;

          return (
            <div
              key={idx}
              className="flex-1 flex flex-col items-center h-full justify-end group relative cursor-pointer"
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              {/* Tooltip on hover */}
              {isHovered && (
                <div className="absolute -top-10 z-20 px-2 py-1 bg-slate-950 border border-slate-700 text-slate-100 text-[11px] font-medium rounded shadow-xl whitespace-nowrap animate-fade-in pointer-events-none">
                  <div className="font-semibold text-indigo-300">{item.label}</div>
                  <div>{item.formattedValue || item.value.toLocaleString()}</div>
                </div>
              )}

              {/* Bar */}
              <div className="w-full max-w-[32px] bg-slate-800/60 rounded-t-md relative flex items-end overflow-hidden h-full">
                <div
                  className={cn(
                    'w-full rounded-t-md transition-all duration-300',
                    isHovered
                      ? 'bg-gradient-to-t from-indigo-600 to-indigo-400 shadow-glow-primary'
                      : 'bg-gradient-to-t from-indigo-700/80 to-indigo-500/80 group-hover:from-indigo-600 group-hover:to-indigo-400'
                  )}
                  style={{ height: `${heightPercent}%` }}
                />
              </div>

              {/* Label */}
              <span className="text-[11px] text-slate-500 mt-2 font-mono group-hover:text-slate-300 transition-colors">
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </Card>
  );
};