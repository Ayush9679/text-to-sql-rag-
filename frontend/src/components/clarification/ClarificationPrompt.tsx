import React, { useState } from 'react';
import { HelpCircle, Sparkles, Send } from 'lucide-react';
import { ClarificationRequest, ClarificationOption } from '../../types';
import { ClarificationOptionCard } from './ClarificationOptionCard';
import { Button } from '../ui/Button';

export interface ClarificationPromptProps {
  request: ClarificationRequest;
  onConfirmSelection?: (option: ClarificationOption) => void;
}

export const ClarificationPrompt: React.FC<ClarificationPromptProps> = ({
  request,
  onConfirmSelection,
}) => {
  const [selectedId, setSelectedId] = useState<string | undefined>(request.selectedOptionId);

  const selectedOption = request.options.find((opt) => opt.id === selectedId);

  const handleSelect = (option: ClarificationOption) => {
    setSelectedId(option.id);
  };

  const handleConfirm = () => {
    if (selectedOption && onConfirmSelection) {
      onConfirmSelection(selectedOption);
    }
  };

  return (
    <div className="p-4 sm:p-5 bg-gradient-to-b from-indigo-950/20 to-slate-900/60 rounded-2xl border border-indigo-500/20 space-y-4 shadow-lg">
      <div className="flex items-start space-x-3">
        <div className="p-2 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400 mt-0.5">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              Clarification Required
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
              {request.ambiguityType.replace('_', ' ')}
            </span>
          </div>
          <h4 className="text-sm sm:text-base font-semibold text-slate-100">{request.question}</h4>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2.5 pt-1">
        {request.options.map((option) => (
          <ClarificationOptionCard
            key={option.id}
            option={option}
            isSelected={selectedId === option.id}
            onSelect={handleSelect}
          />
        ))}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-slate-800">
        <span className="text-xs text-slate-500 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Select an interpretation to generate SQL
        </span>
        <Button
          size="sm"
          variant="primary"
          disabled={!selectedId}
          onClick={handleConfirm}
        >
          <Send className="w-3.5 h-3.5 mr-1.5" /> Confirm & Run
        </Button>
      </div>
    </div>
  );
};
