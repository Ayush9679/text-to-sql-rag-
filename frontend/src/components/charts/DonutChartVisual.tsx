import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { cn } from '../../utils/cn';

export interface DonutSegment {
  label: string;
  value: number;
  color: string;
  formattedValue?: string;
  percentage?: number;
}

export interface DonutChartVisualProps {
  title?: string;
  subtitle?: string;
  data?: DonutSegment[];
  className?: string;
}

const DEFAULT_COLORS = [
  '#6366F1', // indigo
  '#06B6D4', // cyan
  '#10B981', // emerald
  '#F59E0B', // amber
  '#EF4444', // red
  '#EC4899', // pink
  '#8B5CF6', // violet
  '#06D6A0', // teal
];

export const DonutChartVisual: React.FC<DonutChartVisualProps> = ({
  title = 'Breakdown',
  subtitle,
  data = [],
  className,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (data.length === 0) {
    return (
      <Card className={cn('p-5 bg-slate-900/80 border border-slate-800 flex flex-col', className)}>
        <div>
          <h4 className="text-sm font-semibold text-white">{title}</h4>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex-1 flex items-center justify-center my-auto pt-4 text-slate-500 text-sm">
          No breakdown data available
        </div>
      </Card>
    );
  }

  // Ensure colors are assigned
  const segmentsWithColors = data.map((seg, idx) => ({
    ...seg,
    color: seg.color || DEFAULT_COLORS[idx % DEFAULT_COLORS.length],
    formattedValue: seg.formattedValue || seg.value.toLocaleString(),
    percentage: seg.percentage ?? 0,
  }));

  const total = segmentsWithColors.reduce((acc, curr) => acc + curr.value, 0);
  const size = 160;
  const strokeWidth = 24;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let cumulativePercent = 0;

  return (
    <Card className={cn('p-5 bg-slate-900/80 border border-slate-800 flex flex-col', className)}>
      <div>
        <h4 className="text-sm font-semibold text-white">{title}</h4>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-6 my-auto pt-4">
        {/* SVG Donut */}
        <div className="relative flex items-center justify-center">
          <svg width={size} height={size} className="-rotate-90">
            {segmentsWithColors.map((seg, idx) => {
              const segmentPercent = seg.value / total;
              const dashoffset = circumference * (1 - segmentPercent);
              const rotation = cumulativePercent * 360;
              cumulativePercent += segmentPercent;
              const isHovered = hoveredIdx === idx;

              return (
                <circle
                  key={idx}
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  stroke={seg.color}
                  strokeWidth={isHovered ? strokeWidth + 4 : strokeWidth}
                  strokeDasharray={`${circumference} ${circumference}`}
                  strokeDashoffset={dashoffset}
                  strokeLinecap="round"
                  fill="none"
                  transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
                  className="transition-all duration-300 cursor-pointer"
                  onMouseEnter={() => setHoveredIdx(idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                />
              );
            })}
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            {hoveredIdx !== null ? (
              <>
                <span className="text-sm font-bold text-white tabular-nums">
                  {segmentsWithColors[hoveredIdx].percentage}%
                </span>
                <span className="text-[10px] text-slate-400 text-center px-2 truncate max-w-[80px]">
                  {segmentsWithColors[hoveredIdx].label}
                </span>
              </>
            ) : (
              <>
                <span className="text-base font-bold text-white">100%</span>
                <span className="text-[10px] text-slate-400">Total</span>
              </>
            )}
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-col space-y-2.5 w-full sm:w-auto">
          {segmentsWithColors.map((seg, idx) => (
            <div
              key={idx}
              className={cn(
                'flex items-center justify-between space-x-4 text-xs p-1.5 rounded-lg transition-colors cursor-pointer',
                hoveredIdx === idx ? 'bg-slate-800' : 'hover:bg-slate-800/40'
              )}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <div className="flex items-center space-x-2">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: seg.color }}
                />
                <span className="text-slate-300 font-medium truncate max-w-[120px]">{seg.label}</span>
              </div>
              <span className="font-mono text-slate-400 font-medium">
                {seg.formattedValue} ({seg.percentage}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};