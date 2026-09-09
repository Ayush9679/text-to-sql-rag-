import React, { useState } from 'react';
import { Search, Sparkles, BookOpen, ShieldCheck, BookMarked } from 'lucide-react';
import { KnowledgeDocument, BusinessRule, SynonymMapping, RetrievedContextItem } from '../../types';
import { KnowledgeDocumentCard } from './KnowledgeDocumentCard';
import { BusinessRuleItem } from './BusinessRuleItem';
import { TermSynonymList } from './TermSynonymList';
import { RetrievedContextViewer } from './RetrievedContextViewer';
import { Input } from '../ui/Input';
import { Tabs } from '../ui/Tabs';

export interface RagExplorerProps {
  documents: KnowledgeDocument[];
  rules: BusinessRule[];
  synonyms: SynonymMapping[];
  retrievedContexts: RetrievedContextItem[];
}

export const RagExplorer: React.FC<RagExplorerProps> = ({
  documents,
  rules,
  synonyms,
  retrievedContexts,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  const tabs = [
    { id: 'all', label: 'All Knowledge', icon: <BookOpen className="w-3.5 h-3.5" />, badge: documents.length },
    { id: 'rules', label: 'Business Rules', icon: <ShieldCheck className="w-3.5 h-3.5" />, badge: rules.length },
    { id: 'synonyms', label: 'Synonym Dictionary', icon: <BookMarked className="w-3.5 h-3.5" />, badge: synonyms.length },
    { id: 'retrieved', label: 'Retrieved Contexts', icon: <Sparkles className="w-3.5 h-3.5" />, badge: retrievedContexts.length },
  ];

  const filteredDocs = documents.filter((doc) =>
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.tags.some((t) => t.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" /> Knowledge & RAG Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Domain ontology, business calculation logic, schema annotations, and vector grounding context.
          </p>
        </div>

        <div className="w-full sm:w-72">
          <Input
            placeholder="Search knowledge documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Search className="w-3.5 h-3.5" />}
            className="h-9 text-xs"
          />
        </div>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab Panels */}
      {activeTab === 'all' && (
        <div className="space-y-6">
          <RetrievedContextViewer items={retrievedContexts} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredDocs.map((doc) => (
              <KnowledgeDocumentCard key={doc.id} doc={doc} />
            ))}
          </div>

          <TermSynonymList synonyms={synonyms} />
          
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Business Rule Guardrails</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {rules.map((rule) => (
                <BusinessRuleItem key={rule.id} rule={rule} />
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'rules' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rules.map((rule) => (
            <BusinessRuleItem key={rule.id} rule={rule} />
          ))}
        </div>
      )}

      {activeTab === 'synonyms' && (
        <TermSynonymList synonyms={synonyms} />
      )}

      {activeTab === 'retrieved' && (
        <RetrievedContextViewer items={retrievedContexts} />
      )}
    </div>
  );
};
