import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { cn } from '../../utils/cn';

export interface LineChartDataPoint {
  label: string;
  value: number;
  secondaryValue?: number;
}

export interface LineChartVisualProps {
  title?: string;
  subtitle?: string;
  data?: LineChartDataPoint[];
  className?: string;
}

export const LineChartVisual: React.FC<LineChartVisualProps> = ({
  title = 'Query Volume',
  subtitle,
  data = [],
  className,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (data.length === 0) {
    return (
      <Card className={cn('p-5 bg-slate-900/80 border border-slate-800 flex flex-col', className)}>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h4 className="text-sm font-semibold text-white">{title}</h4>
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center min-h-[180px] text-slate-500 text-sm">
          No query volume data available
        </div>
      </Card>
    );
  }

  const maxValue = Math.max(...data.map((d) => Math.max(d.value, d.secondaryValue || 0)), 100);
  const width = 500;
  const height = 180;
  const paddingX = 30;
  const paddingY = 20;

  const points = data.map((d, i) => {
    const x = paddingX + (i / Math.max(data.length - 1, 1)) * (width - paddingX * 2);
    const y = height - paddingY - (d.value / maxValue) * (height - paddingY * 2);
    return { x, y, data: d };
  });

  const secondaryPoints = data.map((d, i) => {
    const x = paddingX + (i / Math.max(data.length - 1, 1)) * (width - paddingX * 2);
    const y = height - paddingY - ((d.secondaryValue || 0) / maxValue) * (height - paddingY * 2);
    return { x, y, data: d };
  });

  const generatePath = (pts: { x: number; y: number }[]) => {
    if (pts.length === 0) return '';
    return pts.reduce((acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`), '');
  };

  const generateAreaPath = (pts: { x: number; y: number }[]) => {
    if (pts.length === 0) return '';
    const line = generatePath(pts);
    const firstX = pts[0].x;
    const lastX = pts[pts.length - 1].x;
    const bottomY = height - paddingY;
    return `${line} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;
  };

  return (
    <Card className={cn('p-5 bg-slate-900/80 border border-slate-800 flex flex-col', className)}>
      <div className="flex items-center justify-between mb-2">
        <div>
          <h4 className="text-sm font-semibold text-white">{title}</h4>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex items-center space-x-3 text-xs text-slate-400">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
            <span>Current</span>
          </div>
          {data[0]?.secondaryValue !== undefined && (
            <div className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-indigo-500/60 inline-block" />
              <span>Previous</span>
            </div>
          )}
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden pt-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
          <defs>
            <linearGradient id="cyanGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = paddingY + pct * (height - paddingY * 2);
            return (
              <line
                key={i}
                x1={paddingX}
                y1={y}
                x2={width - paddingX}
                y2={y}
                stroke="#1E293B"
                strokeDasharray="3 3"
                strokeWidth="1"
              />
            );
          })}

          {/* Area fill for primary */}
          <path d={generateAreaPath(points)} fill="url(#cyanGradient)" />

          {/* Secondary line */}
          {data[0]?.secondaryValue !== undefined && (
            <path
              d={generatePath(secondaryPoints)}
              fill="none"
              stroke="#6366F1"
              strokeWidth="2"
              strokeDasharray="4 4"
              opacity="0.6"
            />
          )}

          {/* Primary line */}
          <path d={generatePath(points)} fill="none" stroke="#06B6D4" strokeWidth="2.5" strokeLinecap="round" />

          {/* Points */}
          {points.map((p, i) => (
            <g key={i} className="cursor-pointer" onMouseEnter={() => setHoveredIdx(i)} onMouseLeave={() => setHoveredIdx(null)}>
              <circle
                cx={p.x}
                cy={p.y}
                r={hoveredIdx === i ? 6 : 4}
                className={cn('fill-slate-950 stroke-cyan-400 stroke-2 transition-all', hoveredIdx === i && 'r-6 stroke-[3]')}
              />
              <text
                x={p.x}
                y={height - 4}
                textAnchor="middle"
                className="text-[10px] fill-slate-500 font-mono"
              >
                {p.data.label}
              </text>
            </g>
          ))}
        </svg>

        {hoveredIdx !== null && (
          <div
            className="absolute top-2 left-1/2 -translate-x-1/2 bg-slate-950 border border-slate-700 px-3 py-1.5 rounded-lg shadow-xl text-xs flex items-center space-x-3 pointer-events-none"
          >
            <span className="font-semibold text-slate-200">{data[hoveredIdx].label}</span>
            <span className="text-cyan-400 font-mono font-medium">{data[hoveredIdx].value.toLocaleString()}</span>
            {data[hoveredIdx].secondaryValue !== undefined && (
              <span className="text-slate-400 font-mono font-medium">({data[hoveredIdx].secondaryValue!.toLocaleString()} prev)</span>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};