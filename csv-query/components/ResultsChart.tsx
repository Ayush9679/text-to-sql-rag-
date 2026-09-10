'use client';

import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon } from 'lucide-react';
import { ChartSuggestion } from '@/types';

interface ResultsChartProps {
  data: Record<string, unknown>[];
  suggestion: ChartSuggestion;
}

const COLORS = [
  '#6366f1', // Indigo
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#3b82f6', // Blue
];

export const ResultsChart: React.FC<ResultsChartProps> = ({ data, suggestion }) => {
  if (!data || data.length === 0 || suggestion.type === 'none' || suggestion.type === 'table') {
    return null;
  }

  // Detect x and y keys
  const keys = Object.keys(data[0] || {});
  if (keys.length === 0) return null;

  const xKey = suggestion.x && keys.includes(suggestion.x) ? suggestion.x : keys[0];
  const yKey =
    suggestion.y && keys.includes(suggestion.y)
      ? suggestion.y
      : keys.find((k) => k !== xKey && typeof data[0][k] === 'number') || keys[1] || keys[0];

  // Convert values for chart
  const chartData = data.slice(0, 50).map((row) => ({
    ...row,
    [xKey]: String(row[xKey] ?? ''),
    [yKey]: typeof row[yKey] === 'number' ? row[yKey] : Number(row[yKey]) || 0,
  }));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {suggestion.type === 'bar' && <BarChart3 className="w-5 h-5 text-indigo-400" />}
          {suggestion.type === 'line' && <LineChartIcon className="w-5 h-5 text-indigo-400" />}
          {suggestion.type === 'pie' && <PieChartIcon className="w-5 h-5 text-indigo-400" />}
          <h3 className="text-sm font-semibold text-white capitalize">
            {suggestion.type} Chart Visualization
          </h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {xKey} vs {yKey}
        </span>
      </div>

      <div className="h-80 w-full pt-4">
        <ResponsiveContainer width="100%" height="100%">
          {suggestion.type === 'bar' ? (
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey={xKey}
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                angle={-20}
                textAnchor="end"
              />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#090d16',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  color: '#f8fafc',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey={yKey} fill="#6366f1" radius={[6, 6, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          ) : suggestion.type === 'line' ? (
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey={xKey}
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                angle={-20}
                textAnchor="end"
              />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#090d16',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  color: '#f8fafc',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Line
                type="monotone"
                dataKey={yKey}
                stroke="#6366f1"
                strokeWidth={3}
                dot={{ fill: '#818cf8', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          ) : (
            <PieChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#090d16',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  color: '#f8fafc',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Pie
                data={chartData}
                dataKey={yKey}
                nameKey={xKey}
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent }) =>
                  `${name}: ${((percent || 0) * 100).toFixed(0)}%`
                }
                labelLine={false}
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
