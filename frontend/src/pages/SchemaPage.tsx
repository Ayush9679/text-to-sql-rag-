import React from 'react';
import { DatabaseSchema } from '../types';
import { SchemaExplorer } from '../components/schema/SchemaExplorer';

const sampleDatabaseSchema: DatabaseSchema = {
  name: 'ecommerce_analytics_prod',
  dialect: 'postgresql',
  version: '16.2',
  tables: [
    {
      name: 'customers',
      schema: 'public',
      description: 'Stores end-user profile details, contact information, geographic regions, and tier statuses.',
      rowCount: 45290,
      columns: [
        { name: 'customer_id', type: 'BIGINT', isPrimaryKey: true, isForeignKey: false, isNullable: false },
        { name: 'first_name', type: 'VARCHAR(100)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'last_name', type: 'VARCHAR(100)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'email', type: 'VARCHAR(255)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'city', type: 'VARCHAR(100)', isPrimaryKey: false, isForeignKey: false, isNullable: true },
        { name: 'country', type: 'VARCHAR(100)', isPrimaryKey: false, isForeignKey: false, isNullable: true },
        { name: 'tier', type: 'VARCHAR(20)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'created_at', type: 'TIMESTAMPTZ', isPrimaryKey: false, isForeignKey: false, isNullable: false },
      ],
    },
    {
      name: 'orders',
      schema: 'public',
      description: 'Master record of orders placed by customers, fulfillment states, and gross monetary values.',
      rowCount: 184920,
      columns: [
        { name: 'order_id', type: 'BIGINT', isPrimaryKey: true, isForeignKey: false, isNullable: false },
        {
          name: 'customer_id',
          type: 'BIGINT',
          isPrimaryKey: false,
          isForeignKey: true,
          foreignKeyTarget: { table: 'customers', column: 'customer_id' },
          isNullable: false,
        },
        { name: 'order_date', type: 'TIMESTAMPTZ', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'status', type: 'VARCHAR(50)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'total_amount', type: 'NUMERIC(12,2)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'discount_amount', type: 'NUMERIC(10,2)', isPrimaryKey: false, isForeignKey: false, isNullable: true },
        { name: 'shipping_city', type: 'VARCHAR(100)', isPrimaryKey: false, isForeignKey: false, isNullable: true },
      ],
    },
    {
      name: 'order_items',
      schema: 'public',
      description: 'Line item breakdown for each order including unit prices, quantities, and product references.',
      rowCount: 549300,
      columns: [
        { name: 'item_id', type: 'BIGINT', isPrimaryKey: true, isForeignKey: false, isNullable: false },
        {
          name: 'order_id',
          type: 'BIGINT',
          isPrimaryKey: false,
          isForeignKey: true,
          foreignKeyTarget: { table: 'orders', column: 'order_id' },
          isNullable: false,
        },
        {
          name: 'product_id',
          type: 'BIGINT',
          isPrimaryKey: false,
          isForeignKey: true,
          foreignKeyTarget: { table: 'products', column: 'product_id' },
          isNullable: false,
        },
        { name: 'quantity', type: 'INTEGER', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'unit_price', type: 'NUMERIC(10,2)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
      ],
    },
    {
      name: 'products',
      schema: 'public',
      description: 'Catalog metadata including SKU, category classification, inventory levels, and active status.',
      rowCount: 12400,
      columns: [
        { name: 'product_id', type: 'BIGINT', isPrimaryKey: true, isForeignKey: false, isNullable: false },
        { name: 'product_name', type: 'VARCHAR(255)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'category', type: 'VARCHAR(100)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'sku', type: 'VARCHAR(50)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'cost_price', type: 'NUMERIC(10,2)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'retail_price', type: 'NUMERIC(10,2)', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'stock_quantity', type: 'INTEGER', isPrimaryKey: false, isForeignKey: false, isNullable: false },
        { name: 'is_active', type: 'BOOLEAN', isPrimaryKey: false, isForeignKey: false, isNullable: false },
      ],
    },
  ],
  relationships: [
    {
      id: 'rel-1',
      sourceTable: 'orders',
      sourceColumn: 'customer_id',
      targetTable: 'customers',
      targetColumn: 'customer_id',
      type: 'many-to-one',
    },
    {
      id: 'rel-2',
      sourceTable: 'order_items',
      sourceColumn: 'order_id',
      targetTable: 'orders',
      targetColumn: 'order_id',
      type: 'many-to-one',
    },
    {
      id: 'rel-3',
      sourceTable: 'order_items',
      sourceColumn: 'product_id',
      targetTable: 'products',
      targetColumn: 'product_id',
      type: 'many-to-one',
    },
  ],
};

export const SchemaPage: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <SchemaExplorer schema={sampleDatabaseSchema} />
    </div>
  );
};
