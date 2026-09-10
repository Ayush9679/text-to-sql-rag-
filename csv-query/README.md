# csv-query — Instant AI Text-to-SQL for CSVs

A complete, production-ready Next.js 14 (App Router, TypeScript) application that lets a business user upload any CSV file and ask natural-language questions about it. Answers are returned with live SQL execution, interactive data tables, and charts.

## Features
- **Generic JSONB Row Store**: Zero dynamic `CREATE TABLE` risk; every CSV is ingested safely into Postgres JSONB rows.
- **SQL Guardrails**: Strict AST and regex validator enforcing read-only `SELECT` queries restricted exclusively to `dataset_rows` with the active `dataset_id`.
- **Master Prompt v2**: Grounded with inferred column types and sample rows, generating instant answers, SQL, and chart suggestions.
- **Visual Analytics**: Interactive bar, line, and pie charts via Recharts, alongside sortable tabular views.
- **Inline Clarifications**: Interactive prompt when the model determines that a question is ambiguous or missing key column context.

---

## Tech Stack
- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Database**: Vercel Postgres (`@vercel/postgres`)
- **Raw File Storage**: Vercel Blob (`@vercel/blob`)
- **AI / LLM**: Anthropic Claude SDK (`@anthropic-ai/sdk`)
- **Parsing**: PapaParse (`papaparse`)
- **Charts**: Recharts (`recharts`)

---

## Deployment to Vercel (Quickstart)

### 1. Install Dependencies
```bash
npm install
```

### 2. Connect Storage Integrations on Vercel
1. Create a project on [vercel.com](https://vercel.com) and import this repository.
2. In your Vercel project dashboard, navigate to the **Storage** tab:
   - Add **Postgres** (Vercel Postgres / Marketplace).
   - Add **Blob** (Vercel Blob).
   *(This automatically injects `POSTGRES_URL` and `BLOB_READ_WRITE_TOKEN` into your environment).*

### 3. Add Anthropic API Key
In your Vercel project dashboard, go to **Settings → Environment Variables** and add:
- `ANTHROPIC_API_KEY`: Your Anthropic API key (`sk-ant-...`).
- `ANTHROPIC_MODEL` *(optional)*: Defaults to `claude-sonnet-4-6`.

### 4. Deploy
Deploy using the Vercel CLI or by pushing to your Git branch:
```bash
vercel deploy
```
*(No manual database migration step is required — the database schema initializes lazily on the first request).*

---

## Local Development

1. Pull your remote Vercel environment variables to your local machine:
   ```bash
   vercel env pull .env.local
   ```
2. Alternatively, copy `.env.example` to `.env.local` and provide your credentials:
   ```bash
   cp .env.example .env.local
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Architecture & Data Model

### Generic JSONB Schema (`lib/schema.sql`)
```sql
CREATE TABLE IF NOT EXISTS datasets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  columns JSONB NOT NULL,
  row_count INT NOT NULL,
  blob_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dataset_rows (
  id BIGSERIAL PRIMARY KEY,
  dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
  row_index INT NOT NULL,
  data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dataset_rows_dataset_id ON dataset_rows(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_rows_data ON dataset_rows USING GIN (data);
```
