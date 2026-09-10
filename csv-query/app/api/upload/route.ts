import { NextRequest, NextResponse } from 'next/server';
import { put } from '@vercel/blob';
import { ensureSchema, sql } from '@/lib/db';
import { parseCSV } from '@/lib/csv';

export const dynamic = 'force-dynamic';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB limit
const BATCH_SIZE = 250;

export async function POST(req: NextRequest) {
  try {
    await ensureSchema();

    const formData = await req.formData();
    const file = formData.get('file') as File | null;

    if (!file) {
      return NextResponse.json(
        { error: 'No file uploaded. Please upload a CSV file.' },
        { status: 400 }
      );
    }

    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: 'File size exceeds 10MB limit. Please upload a smaller file.' },
        { status: 400 }
      );
    }

    // Read and parse CSV content
    const csvContent = await file.text();
    if (!csvContent.trim()) {
      return NextResponse.json(
        { error: 'Uploaded file is empty.' },
        { status: 400 }
      );
    }

    const { columns, rows, rowCount } = parseCSV(csvContent);

    if (rowCount === 0) {
      return NextResponse.json(
        { error: 'No data rows found in the CSV file.' },
        { status: 400 }
      );
    }

    // Upload raw CSV to Vercel Blob if token is configured
    let blobUrl: string | null = null;
    if (process.env.BLOB_READ_WRITE_TOKEN) {
      try {
        const blob = await put(file.name, file, { access: 'public' });
        blobUrl = blob.url;
      } catch (blobError) {
        console.warn('Vercel Blob upload skipped or failed:', blobError);
      }
    }

    // Insert dataset record
    const datasetResult = await sql`
      INSERT INTO datasets (name, columns, row_count, blob_url)
      VALUES (
        ${file.name},
        ${JSON.stringify(columns)},
        ${rowCount},
        ${blobUrl}
      )
      RETURNING id;
    `;

    const datasetId = datasetResult.rows[0].id;

    // Bulk-insert rows in batches
    for (let i = 0; i < rows.length; i += BATCH_SIZE) {
      const batch = rows.slice(i, i + BATCH_SIZE);
      const valueClauses: string[] = [];
      const params: unknown[] = [];
      let pIdx = 1;

      for (let j = 0; j < batch.length; j++) {
        valueClauses.push(
          `($${pIdx++}::uuid, $${pIdx++}::int, $${pIdx++}::jsonb)`
        );
        params.push(datasetId, i + j, JSON.stringify(batch[j]));
      }

      const batchSql = `
        INSERT INTO dataset_rows (dataset_id, row_index, data)
        VALUES ${valueClauses.join(', ')};
      `;

      await sql.query(batchSql, params);
    }

    return NextResponse.json({
      datasetId,
      name: file.name,
      columns,
      rowCount,
    });
  } catch (error) {
    console.error('Upload handler error:', error);
    const message =
      error instanceof Error ? error.message : 'Internal upload processing error.';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
