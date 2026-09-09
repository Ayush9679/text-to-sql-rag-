import React from 'react';
import { CheckCircle2, ChevronRight } from 'lucide-react';
import { ClarificationOption } from '../../types';
import { cn } from '../../utils/cn';

export interface ClarificationOptionCardProps {
  option: ClarificationOption;
  isSelected: boolean;
  onSelect: (option: ClarificationOption) => void;
}

export const ClarificationOptionCard: React.FC<ClarificationOptionCardProps> = ({
  option,
  isSelected,
  onSelect,
}) => {
  return (
    <button
      type="button"
      onClick={() => onSelect(option)}
      className={cn(
        'w-full text-left p-3.5 rounded-xl border transition-all duration-150 flex items-start justify-between group',
        isSelected
          ? 'bg-indigo-600/10 border-indigo-500/50 shadow-sm ring-1 ring-indigo-500/30'
          : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/60'
      )}
    >
      <div className="space-y-1 pr-4">
        <div className="flex items-center space-x-2">
          <span className={cn('text-sm font-medium', isSelected ? 'text-indigo-300' : 'text-slate-200')}>
            {option.label}
          </span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">{option.description}</p>
        {option.sqlHint && (
          <code className="inline-block mt-1 text-[11px] font-mono text-indigo-400/80 bg-slate-950/80 px-2 py-0.5 rounded border border-slate-800">
            {option.sqlHint}
          </code>
        )}
      </div>

      <div className="mt-0.5 flex items-center">
        {isSelected ? (
          <CheckCircle2 className="w-5 h-5 text-indigo-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 flex-shrink-0 transition-transform group-hover:translate-x-0.5" />
        )}
      </div>
    </button>
  );
};
