import React, { useState } from 'react';
import { Copy, Check, ChevronDown, ChevronUp, Terminal, Play, Maximize2, Minimize2 } from 'lucide-react';
import { tokenizeSql } from '../../utils/sqlHighlighter';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

export interface SqlViewerProps {
  sql: string;
  dialect?: string;
  isCollapsible?: boolean;
  defaultExpanded?: boolean;
  onExecute?: () => void;
  showLineNumbers?: boolean;
}

export const SqlViewer: React.FC<SqlViewerProps> = ({
  sql,
  dialect = 'PostgreSQL',
  isCollapsible = true,
  defaultExpanded = true,
  onExecute,
  showLineNumbers = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [copied, setCopied] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const lines = sql.trim().split('\n');

  const renderHighlightedCode = () => {
    return lines.map((line, lineIndex) => {
      const tokens = tokenizeSql(line);
      return (
        <div key={lineIndex} className="table-row">
          {showLineNumbers && (
            <span className="table-cell pr-4 text-right select-none text-slate-600 text-xs font-mono w-8">
              {lineIndex + 1}
            </span>
          )}
          <span className="table-cell font-mono text-xs whitespace-pre">
            {tokens.map((token, tokenIdx) => {
              let colorClass = 'text-slate-300';
              if (token.type === 'keyword') colorClass = 'text-indigo-400 font-semibold';
              else if (token.type === 'string') colorClass = 'text-emerald-400';
              else if (token.type === 'number') colorClass = 'text-amber-400';
              else if (token.type === 'comment') colorClass = 'text-slate-500 italic';
              else if (token.type === 'punctuation') colorClass = 'text-cyan-400';

              return (
                <span key={tokenIdx} className={colorClass}>
                  {token.value}
                </span>
              );
            })}
          </span>
        </div>
      );
    });
  };

  return (
    <div
      className={cn(
        'rounded-xl border border-slate-800 bg-[#0B0F19] overflow-hidden transition-all duration-200 shadow-md',
        isFullScreen && 'fixed inset-4 z-50 rounded-2xl max-w-none shadow-2xl flex flex-col'
      )}
    >
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-slate-900/90 border-b border-slate-800/80">
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[11px] font-mono font-medium text-indigo-300">
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span>{dialect.toUpperCase()}</span>
          </div>
          <span className="text-xs text-slate-400 font-medium">Generated SQL Query</span>
        </div>

        <div className="flex items-center space-x-1.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="h-7 text-xs px-2 text-slate-400 hover:text-slate-200"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400 mr-1" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 mr-1" />
                <span>Copy</span>
              </>
            )}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="h-7 w-7 text-slate-400 hover:text-slate-200"
            aria-label="Toggle Fullscreen"
          >
            {isFullScreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </Button>

          {isCollapsible && !isFullScreen && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-7 w-7 text-slate-400 hover:text-slate-200"
              aria-label="Toggle Code Collapse"
            >
              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </Button>
          )}

          {onExecute && (
            <Button
              variant="subtle"
              size="sm"
              onClick={onExecute}
              className="h-7 text-xs px-2.5 ml-1"
            >
              <Play className="w-3 h-3 mr-1 fill-indigo-400 text-indigo-400" /> Run
            </Button>
          )}
        </div>
      </div>

      {(isExpanded || isFullScreen) && (
        <div className="p-4 overflow-x-auto select-text font-mono text-xs leading-relaxed max-h-96 overflow-y-auto">
          <div className="table w-full">{renderHighlightedCode()}</div>
        </div>
      )}
    </div>
  );
};
