import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, CornerDownLeft } from 'lucide-react';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

export interface QueryInputProps {
  onSend: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onSend,
  isLoading = false,
  placeholder = 'Ask a question about your database in natural language (e.g. "Show top 10 customers by revenue")...',
  className,
}) => {
  const [query, setQuery] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onSend(query.trim());
    setQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        'relative bg-slate-900/90 border border-slate-700/80 rounded-2xl p-2.5 sm:p-3 shadow-xl focus-within:border-indigo-500/60 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all',
        className
      )}
    >
      <div className="flex items-start space-x-2">
        <div className="p-2 text-indigo-400 mt-0.5 select-none hidden sm:block">
          <Sparkles className="w-5 h-5" />
        </div>

        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={isLoading}
          className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 text-sm focus:outline-none resize-none max-h-40 min-h-[44px] py-2 px-1 leading-relaxed"
        />

        <div className="flex items-center space-x-1.5 self-end">
          <Button
            type="submit"
            variant="primary"
            size="sm"
            disabled={!query.trim() || isLoading}
            isLoading={isLoading}
            className="h-10 px-4 rounded-xl"
          >
            <span className="hidden sm:inline mr-1.5">Generate SQL</span>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 px-1">
        <div className="flex items-center space-x-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>PostgreSQL Active (Read-Only)</span>
        </div>
        <div className="flex items-center space-x-1 hidden sm:flex">
          <span>Press</span>
          <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-slate-400">
            Enter <CornerDownLeft className="w-2.5 h-2.5 inline" />
          </kbd>
          <span>to send</span>
        </div>
      </div>
    </form>
  );
};
