import React from 'react';
import { cn } from '../../utils/cn';

export interface ConfidenceGaugeProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

export const ConfidenceGauge: React.FC<ConfidenceGaugeProps> = ({
  score,
  size = 64,
  strokeWidth = 6,
  className,
}) => {
  const normalizedScore = Math.max(0, Math.min(1, score));
  const percent = Math.round(normalizedScore * 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - normalizedScore * circumference;

  const getColor = () => {
    if (normalizedScore >= 0.85) return '#10B981';
    if (normalizedScore >= 0.65) return '#F59E0B';
    return '#F43F5E';
  };

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#1E293B"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getColor()}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          fill="none"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center flex-col">
        <span className="text-xs font-bold text-slate-100 tabular-nums">{percent}%</span>
      </div>
    </div>
  );
};
