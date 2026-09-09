import React from 'react';
import { cn } from '../../utils/cn';

export interface NavigationItemProps {
  id: string;
  label: string;
  icon: React.ReactNode;
  isActive: boolean;
  onClick: () => void;
  badge?: string | number;
}

export const NavigationItem: React.FC<NavigationItemProps> = ({
  label,
  icon,
  isActive,
  onClick,
  badge,
}) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 group select-none',
        isActive
          ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 shadow-sm font-semibold'
          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
      )}
    >
      <div className="flex items-center space-x-3 truncate">
        <span className={cn('w-4 h-4 flex-shrink-0 transition-colors', isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300')}>
          {icon}
        </span>
        <span className="truncate">{label}</span>
      </div>

      {badge !== undefined && (
        <span
          className={cn(
            'text-[10px] px-1.5 py-0.2 rounded-full font-mono',
            isActive ? 'bg-indigo-500/30 text-indigo-200' : 'bg-slate-800 text-slate-400'
          )}
        >
          {badge}
        </span>
      )}
    </button>
  );
};
