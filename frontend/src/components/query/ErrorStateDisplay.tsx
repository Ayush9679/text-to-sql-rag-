import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '../ui/Button';

export interface ErrorStateDisplayProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorStateDisplay: React.FC<ErrorStateDisplayProps> = ({
  title = 'Query Synthesis Error',
  message,
  onRetry,
}) => {
  return (
    <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl space-y-3">
      <div className="flex items-start space-x-3">
        <div className="p-2 bg-rose-500/20 rounded-xl text-rose-400">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1 flex-1">
          <h4 className="text-sm font-semibold text-rose-200">{title}</h4>
          <p className="text-xs text-rose-300/80 leading-relaxed">{message}</p>
        </div>
      </div>

      {onRetry && (
        <div className="flex justify-end pt-1">
          <Button variant="danger" size="sm" onClick={onRetry}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Retry Request
          </Button>
        </div>
      )}
    </div>
  );
};
