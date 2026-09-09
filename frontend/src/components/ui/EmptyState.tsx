import React from 'react';
import { Card } from './Card';
import { cn } from '../../utils/cn';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
  compact?: boolean;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
  compact = false,
}) => {
  return (
    <Card
      className={cn(
        'flex flex-col items-center justify-center text-center border border-dashed border-slate-700/60 bg-slate-900/40',
        compact ? 'p-6' : 'p-10 sm:p-14',
        className,
      )}
    >
      {icon && (
        <div className="mb-4 p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/40 text-slate-400">
          {icon}
        </div>
      )}
      <h3 className={cn('font-semibold text-slate-200', compact ? 'text-sm' : 'text-base')}>
        {title}
      </h3>
      {description && (
        <p className={cn('text-slate-500 mt-1.5 max-w-sm', compact ? 'text-xs' : 'text-sm')}>
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </Card>
  );
};
