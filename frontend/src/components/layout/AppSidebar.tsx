import React from 'react';
import {
  MessageSquareCode,
  Layers,
  Sparkles,
  History,
  Settings,
  Database,
  BarChart3,
  TerminalSquare,
  PlusCircle
} from 'lucide-react';
import { NavigationItem } from './NavigationItem';
import { Button } from '../ui/Button';

export interface AppSidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  onNewChat?: () => void;
}

export const AppSidebar: React.FC<AppSidebarProps> = ({
  activePage,
  onNavigate,
  onNewChat,
}) => {
  const navItems = [
    { id: 'workspace', label: 'Chat Workspace', icon: <MessageSquareCode /> },
    { id: 'schema', label: 'Schema Explorer', icon: <Layers /> },
    { id: 'rag', label: 'Knowledge & RAG', icon: <Sparkles /> },
    { id: 'analytics', label: 'Analytics Dashboard', icon: <BarChart3 /> },
    { id: 'history', label: 'Query History', icon: <History /> },
    { id: 'settings', label: 'Settings & Config', icon: <Settings /> },
  ];

  return (
    <aside className="w-64 h-full bg-slate-950/95 border-r border-slate-800/80 flex flex-col justify-between p-4 flex-shrink-0 select-none">
      <div className="space-y-6">
        {/* Brand */}
        <div className="flex items-center space-x-3 px-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white shadow-glow-primary">
            <TerminalSquare className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-tight flex items-center gap-1.5">
              SQLMind <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-mono">v1.0</span>
            </h1>
            <p className="text-[11px] text-slate-500">Conversational SQL Analyst</p>
          </div>
        </div>

        {/* New Session Button */}
        {onNewChat && (
          <Button
            variant="primary"
            size="md"
            onClick={onNewChat}
            className="w-full justify-start text-xs rounded-xl"
          >
            <PlusCircle className="w-4 h-4 mr-2" />
            <span>New Query Session</span>
          </Button>
        )}

        {/* Navigation Section */}
        <div className="space-y-1">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
            Navigation
          </div>
          {navItems.map((item) => (
            <NavigationItem
              key={item.id}
              id={item.id}
              label={item.label}
              icon={item.icon}
              isActive={activePage === item.id}
              onClick={() => onNavigate(item.id)}
            />
          ))}
        </div>
      </div>

      {/* Database Connection Status in Footer */}
      <div className="pt-4 border-t border-slate-800/80 space-y-3">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-1.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-emerald-400" /> PostgreSQL
            </span>
            <span className="text-emerald-400 font-mono text-[10px] bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
              Online
            </span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono truncate">prod-db-replica.internal:5432</p>
        </div>
      </div>
    </aside>
  );
};
