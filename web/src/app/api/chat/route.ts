import { NextRequest } from 'next/server';
import { askInkeep } from '@/lib/inkeep/client';

export const runtime = 'edge';

export async function POST(req: NextRequest) {
  try {
    const { url, message } = await req.json();
    
    if (!url || !message) {
      return new Response('Missing url or message', { status: 400 });
    }

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // askInkeep is an async generator
          for await (const chunk of askInkeep(url, message)) {
            // Convert chunk object to NDJSON string
            const text = JSON.stringify(chunk) + '
';
            controller.enqueue(encoder.encode(text));
          }
        } catch (e) {
          const errorJson = JSON.stringify({ type: 'error', content: String(e) }) + '
';
          controller.enqueue(encoder.encode(errorJson));
        } finally {
          controller.close();
        }
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'application/x-ndjson',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    return new Response(String(error), { status: 500 });
  }
}
