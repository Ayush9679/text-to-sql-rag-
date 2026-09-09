import React, { useState } from 'react';
import { Settings, Database, Cpu, Sliders, Shield, Palette, Save, Check } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Tabs } from '../components/ui/Tabs';

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('database');
  const [saved, setSaved] = useState(false);

  const tabs = [
    { id: 'database', label: 'Database Config', icon: <Database className="w-3.5 h-3.5" /> },
    { id: 'ai', label: 'AI Model & Groq', icon: <Cpu className="w-3.5 h-3.5" /> },
    { id: 'query', label: 'Query Preferences', icon: <Sliders className="w-3.5 h-3.5" /> },
    { id: 'security', label: 'Security & Safety', icon: <Shield className="w-3.5 h-3.5" /> },
    { id: 'appearance', label: 'Appearance', icon: <Palette className="w-3.5 h-3.5" /> },
  ];

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-indigo-400" /> System Settings & Configuration
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure target database credentials, AI model hyperparameters, query guardrails, and display preferences.
          </p>
        </div>

        <Button variant="primary" size="sm" onClick={handleSave} className="h-9 px-4 text-xs">
          {saved ? (
            <>
              <Check className="w-3.5 h-3.5 mr-1.5 text-emerald-300" /> Saved Changes
            </>
          ) : (
            <>
              <Save className="w-3.5 h-3.5 mr-1.5" /> Save Changes
            </>
          )}
        </Button>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Database Config Tab */}
      {activeTab === 'database' && (
        <Card className="p-6 bg-slate-900/80 border border-slate-800 space-y-5">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-white">Target Database Connection (PostgreSQL)</h3>
            <p className="text-xs text-slate-400">Configure connection details for schema introspection and read-only execution.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Host" defaultValue="prod-db-replica.internal" />
            <Input label="Port" defaultValue="5432" type="number" />
            <Input label="Database Name" defaultValue="ecommerce_analytics_prod" />
            <Input label="Username" defaultValue="analytics_ro_user" />
            <Input label="Password" type="password" defaultValue="••••••••••••" />
            
            <div className="w-full space-y-1.5">
              <label className="block text-xs font-medium text-slate-300">SSL Mode</label>
              <select className="w-full bg-slate-900 text-slate-100 border border-slate-700/80 rounded-lg text-sm px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/40">
                <option value="require">require (verify-ca)</option>
                <option value="prefer">prefer</option>
                <option value="disable">disable</option>
              </select>
            </div>
          </div>

          <div className="pt-2 flex items-center space-x-2">
            <input type="checkbox" id="readonly" defaultChecked className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500" />
            <label htmlFor="readonly" className="text-xs text-slate-300">
              Enforce Strict READ-ONLY Transaction Mode (DISALLOW INSERT/UPDATE/DELETE/DROP)
            </label>
          </div>
        </Card>
      )}

      {/* AI Model Tab */}
      {activeTab === 'ai' && (
        <Card className="p-6 bg-slate-900/80 border border-slate-800 space-y-5">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-white">AI Engine & Model Configuration</h3>
            <p className="text-xs text-slate-400">Manage LLM endpoint, inference temperature, and synthesis prompts.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="w-full space-y-1.5">
              <label className="block text-xs font-medium text-slate-300">Inference Provider</label>
              <select className="w-full bg-slate-900 text-slate-100 border border-slate-700/80 rounded-lg text-sm px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/40">
                <option value="groq">Groq Cloud (Fast LPUs)</option>
                <option value="anthropic">Anthropic Claude</option>
                <option value="openai">OpenAI GPT-4o</option>
              </select>
            </div>

            <div className="w-full space-y-1.5">
              <label className="block text-xs font-medium text-slate-300">Model Architecture</label>
              <select className="w-full bg-slate-900 text-slate-100 border border-slate-700/80 rounded-lg text-sm px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/40">
                <option value="llama-3-70b-8192">llama3-70b-8192 (Recommended)</option>
                <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>
                <option value="gemma2-9b-it">gemma2-9b-it</option>
              </select>
            </div>

            <Input label="Temperature (0.0 for deterministic SQL)" defaultValue="0.0" type="number" step="0.1" min="0" max="1" />
            <Input label="Max Completion Tokens" defaultValue="2048" type="number" />
          </div>

          <div className="pt-2 space-y-2">
            <div className="flex items-center space-x-2">
              <input type="checkbox" id="thinking" defaultChecked className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500" />
              <label htmlFor="thinking" className="text-xs text-slate-300">
                Enable Step-by-Step Chain-of-Thought Query Explanation
              </label>
            </div>
          </div>
        </Card>
      )}

      {/* Query Preferences Tab */}
      {activeTab === 'query' && (
        <Card className="p-6 bg-slate-900/80 border border-slate-800 space-y-5">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-white">Query Execution Preferences</h3>
            <p className="text-xs text-slate-400">Limits, timeouts, formatting, and ambiguity thresholds.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Default Row LIMIT (when unstated in prompt)" defaultValue="100" type="number" />
            <Input label="Execution Timeout (Milliseconds)" defaultValue="10000" type="number" />
            <Input label="Ambiguity Clarification Threshold (0.0 - 1.0)" defaultValue="0.75" type="number" step="0.05" />
          </div>

          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <input type="checkbox" id="clarifyLow" defaultChecked className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500" />
              <label htmlFor="clarifyLow" className="text-xs text-slate-300">
                Prompt for clarification when confidence score is below threshold
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input type="checkbox" id="formatSql" defaultChecked className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500" />
              <label htmlFor="formatSql" className="text-xs text-slate-300">
                Auto-format and uppercase SQL keywords in viewer
              </label>
            </div>
          </div>
        </Card>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <Card className="p-6 bg-slate-900/80 border border-slate-800 space-y-5">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-white">Security & Guardrails</h3>
            <p className="text-xs text-slate-400">Data masking, destructive query prevention, and audit logs.</p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <input type="checkbox" id="blockDestructive" defaultChecked disabled className="rounded bg-slate-800 border-slate-700 text-indigo-600" />
              <label htmlFor="blockDestructive" className="text-xs text-slate-300">
                Strict AST Block on DROP, ALTER, TRUNCATE, UPDATE, DELETE (Hardcoded Enforced)
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input type="checkbox" id="maskSensitive" defaultChecked className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500" />
              <label htmlFor="maskSensitive" className="text-xs text-slate-300">
                Mask sensitive column values (passwords, social security, credit cards)
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input type="checkbox" id="auditLog" defaultChecked className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500" />
              <label htmlFor="auditLog" className="text-xs text-slate-300">
                Enable JSONL structured query audit logging
              </label>
            </div>
          </div>
        </Card>
      )}

      {/* Appearance Tab */}
      {activeTab === 'appearance' && (
        <Card className="p-6 bg-slate-900/80 border border-slate-800 space-y-5">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-white">Appearance & Theme</h3>
            <p className="text-xs text-slate-400">Dark analytics theme, code editor styling, and font hierarchy.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-4 rounded-xl border-2 border-indigo-500 bg-slate-950/80 space-y-2 cursor-pointer">
              <div className="w-full h-16 bg-[#090D16] rounded-lg border border-slate-800 flex items-center justify-center">
                <span className="text-xs font-mono text-indigo-400">Dark Obsidian</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-white">Obsidian Dark</span>
                <Check className="w-4 h-4 text-indigo-400" />
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-2 cursor-pointer opacity-60 hover:opacity-100">
              <div className="w-full h-16 bg-slate-900 rounded-lg border border-slate-800 flex items-center justify-center">
                <span className="text-xs font-mono text-cyan-400">Cyber Cyan</span>
              </div>
              <span className="text-xs font-semibold text-slate-400 block">Midnight Cyan</span>
            </div>

            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-2 cursor-pointer opacity-60 hover:opacity-100">
              <div className="w-full h-16 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center">
                <span className="text-xs font-mono text-emerald-400">Emerald Matrix</span>
              </div>
              <span className="text-xs font-semibold text-slate-400 block">Emerald Matrix</span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
