import { NextResponse } from 'next/server';
import { ensureSchema, sql } from '@/lib/db';
import { Dataset } from '@/types';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    await ensureSchema();

    const result = await sql<Dataset>`
      SELECT 
        id, 
        name, 
        columns, 
        row_count, 
        blob_url, 
        created_at
      FROM datasets
      ORDER BY created_at DESC;
    `;

    return NextResponse.json({ datasets: result.rows });
  } catch (error) {
    console.error('Error fetching datasets:', error);
    return NextResponse.json(
      { error: 'Failed to fetch datasets.' },
      { status: 500 }
    );
  }
}
