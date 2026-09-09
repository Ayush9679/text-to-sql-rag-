import React from 'react';
import { KnowledgeDocument, BusinessRule, SynonymMapping, RetrievedContextItem } from '../types';
import { RagExplorer } from '../components/rag/RagExplorer';

const sampleDocs: KnowledgeDocument[] = [
  {
    id: 'doc-1',
    title: 'Recognized Net Revenue Formula',
    category: 'business_rule',
    content: 'Net revenue must only calculate completed orders. `status = "COMPLETED"` and `discount_amount` must be deducted from `total_amount`. Refunded and cancelled statuses are strictly omitted.',
    relevanceScore: 0.96,
    source: 'Finance / ERP Handbook v3.2',
    updatedAt: '2026-08-01',
    tags: ['revenue', 'finance', 'orders', 'formula'],
  },
  {
    id: 'doc-2',
    title: 'Customer Churn Definition',
    category: 'metric_definition',
    content: 'An active customer is considered churned if no new order has been registered in the `orders` table within 90 consecutive calendar days from the reference date.',
    relevanceScore: 0.91,
    source: 'Growth Analytics Charter',
    updatedAt: '2026-07-20',
    tags: ['churn', 'customers', 'retention'],
  },
  {
    id: 'doc-3',
    title: 'Product Margin & Profitability',
    category: 'schema_annotation',
    content: 'Gross margin is calculated as: `(retail_price - cost_price) / retail_price * 100.0`. Inventory cost accounting follows standard FIFO weighted average stored in `products.cost_price`.',
    relevanceScore: 0.88,
    source: 'Supply Chain & Merchandising Spec',
    updatedAt: '2026-06-15',
    tags: ['margin', 'products', 'cogs', 'profit'],
  },
];

const sampleRules: BusinessRule[] = [
  {
    id: 'rule-1',
    name: 'Exclude Soft-Deleted / Archived Records',
    description: 'Ensure any queries querying products or customers automatically apply is_active = TRUE filters unless explicitly requested.',
    conditionFormula: 'WHERE products.is_active = TRUE',
    applicableTables: ['products'],
    priority: 'high',
  },
  {
    id: 'rule-2',
    name: 'Valid Completed Orders Filter',
    description: 'Prevent counting pending, refunded, or chargeback orders towards financial metrics.',
    conditionFormula: "WHERE orders.status IN ('COMPLETED', 'SHIPPED')",
    applicableTables: ['orders'],
    priority: 'high',
  },
  {
    id: 'rule-3',
    name: 'Timezone Standardization',
    description: 'All date comparisons and truncations must cast to UTC timezone.',
    conditionFormula: "DATE_TRUNC('day', order_date AT TIME ZONE 'UTC')",
    applicableTables: ['orders'],
    priority: 'medium',
  },
];

const sampleSynonyms: SynonymMapping[] = [
  {
    id: 'syn-1',
    userTerm: 'Gross Merchandise Value (GMV)',
    canonicalEntity: 'SUM(orders.total_amount)',
    targetType: 'metric',
    context: 'Natural language terms like "sales", "GMV", "turnover", "total sales".',
  },
  {
    id: 'syn-2',
    userTerm: 'Buyers / Clients / Accounts',
    canonicalEntity: 'customers',
    targetType: 'table',
    context: 'Natural language references to clients or buyers map to public.customers table.',
  },
  {
    id: 'syn-3',
    userTerm: 'AOV',
    canonicalEntity: 'AVG(orders.total_amount)',
    targetType: 'metric',
    context: 'Average Order Value acronym.',
  },
  {
    id: 'syn-4',
    userTerm: 'SKU / Item',
    canonicalEntity: 'products.sku',
    targetType: 'column',
    context: 'Item code identifier or SKU representation.',
  },
];

const sampleRetrievedContexts: RetrievedContextItem[] = [
  {
    id: 'ret-1',
    docTitle: 'Finance / ERP Handbook v3.2 [Chunk #14]',
    similarity: 0.942,
    category: 'business_rule',
    snippet: 'When aggregating customer lifetime value or top accounts, group by customer_id and include only status = "COMPLETED" records from orders table.',
  },
  {
    id: 'ret-2',
    docTitle: 'Customer Churn & Retention Dictionary [Chunk #3]',
    similarity: 0.887,
    category: 'metric_definition',
    snippet: 'VIP or Best Customer tiers are classified by total spend >= $10,000 or customer.tier = "PLATINUM".',
  },
];

export const KnowledgePage: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <RagExplorer
        documents={sampleDocs}
        rules={sampleRules}
        synonyms={sampleSynonyms}
        retrievedContexts={sampleRetrievedContexts}
      />
    </div>
  );
};
