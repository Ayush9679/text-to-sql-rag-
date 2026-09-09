import React, { useRef, useEffect } from 'react';
import { QueryMessage, ClarificationOption } from '../../types';
import { ChatMessage } from './ChatMessage';
import { LoadingState } from './LoadingState';
import { EmptyState } from './EmptyState';

export interface ChatContainerProps {
  messages: QueryMessage[];
  isLoading?: boolean;
  onSelectSuggestion: (query: string) => void;
  onClarificationSelect?: (option: ClarificationOption) => void;
  onExecuteSql?: (sql: string) => void;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isLoading = false,
  onSelectSuggestion,
  onClarificationSelect,
  onExecuteSql,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return <EmptyState onSelectSuggestion={onSelectSuggestion} />;
  }

  return (
    <div className="space-y-6 pb-4">
      {messages.map((msg) => (
        <ChatMessage
          key={msg.id}
          message={msg}
          onClarificationSelect={onClarificationSelect}
          onExecuteSql={onExecuteSql}
        />
      ))}

      {isLoading && <LoadingState />}
      <div ref={bottomRef} />
    </div>
  );
};
