import { NextRequest, NextResponse } from 'next/server';

const mockNodes = [
  { id: 'node-asia-1', region: 'Asia' },
  { id: 'node-asia-2', region: 'Asia' },
  { id: 'node-europe-1', region: 'Europe' },
  { id: 'node-europe-2', region: 'Europe' },
  { id: 'node-america-1', region: 'America' },
  { id: 'node-america-2', region: 'America' },
];

const mockContent = {
  'index.html': '<!DOCTYPE html><html><head><title>Home</title></head><body><h1>Welcome</h1></body></html>',
  'app.js': 'console.log("App started"); function init() { /* app initialization */ }',
  'styles.css': 'body { margin: 0; padding: 0; font-family: sans-serif; }',
  'logo.png': '[binary image data]',
  'data.json': '{"status":"ok","version":"1.0.0","timestamp":1234567890}',
};

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const filename = searchParams.get('file');
  const location = request.headers.get('X-Client-Location') || 'America';

  if (!filename) {
    return NextResponse.json({ error: 'Missing filename parameter' }, { status: 400 });
  }

  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, Math.random() * 200 + 50));

  // Select a random node from the requested region
  const regionNodes = mockNodes.filter((n) => n.region === location);
  const selectedNode = regionNodes[Math.floor(Math.random() * regionNodes.length)] || mockNodes[0];

  // Simulate different cache scenarios
  const random = Math.random();
  let status: 'HIT' | 'MISS' | 'BUSY' | 'ERROR';
  let latency: number;

  if (random > 0.85) {
    // 15% chance of error
    status = 'ERROR';
    latency = 0;
    return NextResponse.json(
      {
        request_id: `req-${Date.now()}`,
        selected_node: selectedNode.id,
        status,
        latency,
        content: null,
      },
      { status: 500 }
    );
  } else if (random > 0.7) {
    // 15% chance of busy
    status = 'BUSY';
    latency = 450 + Math.random() * 100;
  } else if (random > 0.4) {
    // 30% chance of cache hit
    status = 'HIT';
    latency = 50 + Math.random() * 100;
  } else {
    // 40% chance of cache miss
    status = 'MISS';
    latency = 300 + Math.random() * 200;
  }

  const content = (mockContent as Record<string, string>)[filename] || `Content of ${filename}`;

  return NextResponse.json({
    request_id: `req-${Date.now()}`,
    selected_node: selectedNode.id,
    status,
    latency: Math.round(latency),
    content,
  });
}
