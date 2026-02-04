import { NextResponse } from 'next/server';
import { DEFAULT_SITES } from '@/lib/inkeep/registry';

export const runtime = 'edge';

export async function GET() {
  const sites = Object.entries(DEFAULT_SITES).map(([id, config]) => ({
    id,
    name: id.charAt(0).toUpperCase() + id.slice(1),
    url: config.url,
    description: config.description
  }));
  
  return NextResponse.json(sites);
}
