import React from 'react';
import { cn } from '../../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'interactive' | 'outline';
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'default',
  ...props
}) => {
  const variants = {
    default: 'bg-slate-900/80 border border-slate-800 rounded-xl shadow-md',
    glass: 'glass-panel rounded-xl',
    interactive: 'bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-indigo-500/30 rounded-xl transition-all cursor-pointer shadow-md',
    outline: 'bg-transparent border border-slate-800 rounded-xl',
  };

  return (
    <div className={cn(variants[variant], className)} {...props}>
      {children}
    </div>
  );
};
