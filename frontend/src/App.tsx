import React, { useEffect, useState } from 'react';
import { MainLayout } from './components/layout/MainLayout';
import { WorkspacePage } from './pages/WorkspacePage';
import { SchemaPage } from './pages/SchemaPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { AnalyticsDashboard } from './components/charts/AnalyticsDashboard';
import { AuthenticatedUser, getCurrentUser, logout } from './services/auth';
import { LoginPage } from './pages/LoginPage';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<string>('workspace');
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [authState, setAuthState] = useState<'loading' | 'authenticated' | 'unauthenticated'>('loading');
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    let mounted = true;
    void getCurrentUser().then((currentUser) => {
      if (!mounted) return;
      setUser(currentUser);
      setAuthState(currentUser ? 'authenticated' : 'unauthenticated');
    }).catch(() => { if (mounted) setAuthState('unauthenticated'); });
    return () => { mounted = false; };
  }, []);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try { await logout(); } finally { setUser(null); setAuthState('unauthenticated'); setIsLoggingOut(false); }
  };

  if (authState === 'loading') return <div className="flex min-h-screen items-center justify-center bg-[#090D16] text-sm text-slate-400"><span className="mr-2 h-3 w-3 animate-pulse rounded-full bg-cyan-400" /> Securing your workspace…</div>;
  if (authState === 'unauthenticated' || !user) return <LoginPage />;

  const renderActivePage = () => {
    switch (activePage) {
      case 'workspace':
        return <WorkspacePage />;
      case 'schema':
        return <SchemaPage />;
      case 'rag':
        return <KnowledgePage />;
      case 'analytics':
        return (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
              <h2 className="text-lg font-bold text-white">Database Analytics & Operational KPIs</h2>
              <p className="text-xs text-slate-400 mt-0.5">Real-time aggregate visual insights synthesized from query execution patterns.</p>
            </div>
            <AnalyticsDashboard />
          </div>
        );
      case 'history':
        return <HistoryPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <WorkspacePage />;
    }
  };

  return (
    <MainLayout
      activePage={activePage}
      onNavigate={setActivePage}
      onNewChat={() => setActivePage('workspace')}
      user={user}
      onLogout={handleLogout}
      isLoggingOut={isLoggingOut}
    >
      {renderActivePage()}
    </MainLayout>
  );
};

export default App;
