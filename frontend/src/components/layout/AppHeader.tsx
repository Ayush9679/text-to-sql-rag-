import React from 'react';
import { ShieldCheck, Bell, Cpu, LogOut, Menu } from 'lucide-react';
import { Button } from '../ui/Button';
import { AuthenticatedUser } from '../../services/auth';

export interface AppHeaderProps {
  onToggleMobileMenu?: () => void;
  user: AuthenticatedUser;
  onLogout: () => void;
  isLoggingOut?: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ onToggleMobileMenu, user, onLogout, isLoggingOut = false }) => {
  return (
    <header className="h-14 bg-slate-950/80 border-b border-slate-800/80 px-4 sm:px-6 flex items-center justify-between z-20 backdrop-blur-md">
      <div className="flex items-center space-x-3">
        {onToggleMobileMenu && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleMobileMenu}
            className="md:hidden text-slate-400"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </Button>
        )}
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold text-slate-300">Connected Database:</span>
          <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
            ecommerce_analytics_prod
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Safety Guardrails: Active</span>
        </div>

        <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>Groq Llama 3 70B</span>
        </div>

        <Button variant="outline" size="icon" className="h-8 w-8 text-slate-400 hover:text-white">
          <Bell className="w-4 h-4" />
        </Button>
        <div className="hidden lg:block max-w-[12rem] text-right leading-tight">
          <p className="truncate text-xs font-medium text-slate-200">{user.name}</p>
          <p className="truncate text-[10px] text-slate-500">{user.businessName || user.email}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onLogout} isLoading={isLoggingOut} className="text-slate-400 hover:text-rose-200">
          {!isLoggingOut && <LogOut className="h-3.5 w-3.5" />}<span className="hidden sm:inline">Sign out</span>
        </Button>
      </div>
    </header>
  );
};
