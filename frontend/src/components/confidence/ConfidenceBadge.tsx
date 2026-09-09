import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';
import { formatConfidenceTier } from '../../utils/formatters';
import { cn } from '../../utils/cn';

export interface ConfidenceBadgeProps {
  score: number;
  showIcon?: boolean;
  showPercent?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  score,
  showIcon = true,
  showPercent = true,
  size = 'sm',
  className,
}) => {
  const info = formatConfidenceTier(score);
  const percent = Math.round(score * 100);

  const getIcon = () => {
    if (info.tier === 'high') return <ShieldCheck className="w-3.5 h-3.5" />;
    if (info.tier === 'medium') return <AlertTriangle className="w-3.5 h-3.5" />;
    return <ShieldAlert className="w-3.5 h-3.5" />;
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full border',
        info.bgColor,
        info.color,
        info.borderColor,
        size === 'sm' ? 'text-[11px] px-2.5 py-0.5 gap-1.5' : 'text-xs px-3 py-1 gap-2',
        className
      )}
    >
      {showIcon && getIcon()}
      <span>{info.label}</span>
      {showPercent && <span className="font-semibold tabular-nums">({percent}%)</span>}
    </span>
  );
};
