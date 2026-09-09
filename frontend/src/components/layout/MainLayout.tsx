import React, { useState } from 'react';
import { AppSidebar } from './AppSidebar';
import { AppHeader } from './AppHeader';
import { AuthenticatedUser } from '../../services/auth';

export interface MainLayoutProps {
  children: React.ReactNode;
  activePage: string;
  onNavigate: (page: string) => void;
  onNewChat?: () => void;
  user: AuthenticatedUser;
  onLogout: () => void;
  isLoggingOut?: boolean;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  activePage,
  onNavigate,
  onNewChat,
  user,
  onLogout,
  isLoggingOut,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090D16] text-slate-100">
      {/* Desktop Sidebar */}
      <div className="hidden md:block h-full">
        <AppSidebar
          activePage={activePage}
          onNavigate={onNavigate}
          onNewChat={onNewChat}
        />
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative z-10 w-64 h-full bg-slate-950">
            <AppSidebar
              activePage={activePage}
              onNavigate={(p) => {
                onNavigate(p);
                setMobileMenuOpen(false);
              }}
              onNewChat={() => {
                onNewChat?.();
                setMobileMenuOpen(false);
              }}
            />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <AppHeader onToggleMobileMenu={() => setMobileMenuOpen(true)} user={user} onLogout={onLogout} isLoggingOut={isLoggingOut} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};
