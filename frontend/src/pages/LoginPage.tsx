import React from 'react';
import { ArrowRight, LockKeyhole, Sparkles, TerminalSquare } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { beginGoogleLogin } from '../services/auth';

export const LoginPage: React.FC = () => (
  <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#090D16] px-5 py-10 text-slate-100">
    <div className="absolute inset-0 opacity-40" aria-hidden="true" style={{ backgroundImage: 'radial-gradient(circle at 15% 15%, rgba(79,70,229,.28), transparent 28rem), radial-gradient(circle at 86% 84%, rgba(6,182,212,.14), transparent 25rem)' }} />
    <section className="relative w-full max-w-md border border-slate-700/70 bg-slate-950/70 p-7 shadow-2xl shadow-black/30 backdrop-blur-sm sm:p-9">
      <div className="mb-10 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 shadow-glow-primary">
          <TerminalSquare className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold tracking-tight text-white">SQLMind</p>
          <p className="text-[11px] text-slate-500">Conversational SQL Analyst</p>
        </div>
      </div>

      <div className="space-y-3">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-cyan-300"><Sparkles className="h-3.5 w-3.5" /> Analyst workspace</span>
        <h1 className="text-3xl font-semibold tracking-tight text-white">Sign in to your data workspace.</h1>
        <p className="max-w-sm text-sm leading-6 text-slate-400">Ask clearer questions, get safe SQL, and keep your team’s datasets in one protected place.</p>
      </div>

      <Button size="lg" className="mt-8 w-full bg-white text-slate-950 shadow-none hover:bg-slate-200" onClick={beginGoogleLogin}>
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4"><path fill="#4285F4" d="M21.8 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.5a4.7 4.7 0 0 1-2 3.1v2.5h3.2c1.9-1.8 3.1-4.3 3.1-7.4Z" /><path fill="#34A853" d="M12 22c2.7 0 5-.9 6.7-2.4l-3.2-2.5c-.9.6-2 .9-3.5.9-2.7 0-5-1.8-5.8-4.3H2.9v2.6A10 10 0 0 0 12 22Z" /><path fill="#FBBC05" d="M6.2 13.7A6 6 0 0 1 5.9 12c0-.6.1-1.1.3-1.7V7.7H2.9A10 10 0 0 0 2 12c0 1.6.4 3.1.9 4.3l3.3-2.6Z" /><path fill="#EA4335" d="M12 6c1.5 0 2.9.5 3.9 1.5l2.9-2.9C17 2.9 14.7 2 12 2a10 10 0 0 0-9.1 5.7l3.3 2.6C7 7.8 9.3 6 12 6Z" /></svg>
        Continue with Google <ArrowRight className="ml-auto h-4 w-4" />
      </Button>

      <p className="mt-6 flex items-center justify-center gap-1.5 text-center text-xs text-slate-500"><LockKeyhole className="h-3.5 w-3.5 text-emerald-400" /> Secure, organization-managed access</p>
    </section>
  </main>
);
