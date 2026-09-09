import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

export interface QuerySuggestionsProps {
  onSelectSuggestion: (query: string) => void;
}

const suggestions = [
  'Show the top 10 customers by revenue.',
  'What were our best-selling products last quarter?',
  'Show monthly revenue for this year.',
  'Which cities generated the most sales?',
  'List customers with more than 5 orders who spent over $1,000.',
  'What is our customer churn rate by subscription tier?'
];

export const QuerySuggestions: React.FC<QuerySuggestionsProps> = ({ onSelectSuggestion }) => {
  return (
    <div className="space-y-2.5">
      <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
        <span>Suggested Queries</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {suggestions.map((query, index) => (
          <button
            key={index}
            onClick={() => onSelectSuggestion(query)}
            className="flex items-center justify-between p-3 text-left bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-indigo-500/40 rounded-xl transition-all group text-xs text-slate-300 hover:text-white"
          >
            <span className="truncate pr-2 font-medium">{query}</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-indigo-400 flex-shrink-0 transition-transform group-hover:translate-x-0.5" />
          </button>
        ))}
      </div>
    </div>
  );
};
