import { Node, TimelineStep } from './types';

// ✅ Real backend endpoints
const API = {
  ROUTE: "http://localhost:8000",
  REGISTRY: "http://localhost:8005",
  PURGE: "http://localhost:8006",
};

export interface FileRequestResponse {
  request_id: string;
  selected_node: string;
  status: 'HIT' | 'MISS' | 'BUSY' | 'ERROR';
  data?: {
    content?: string;
    [key: string]: any;
  };
}

// -----------------------------
// FETCH FILE
// -----------------------------
export async function fetchFile(
  filename: string,
  location: string
): Promise<FileRequestResponse> {
  try {
    const response = await fetch(
      `${API.ROUTE}/route?file=${encodeURIComponent(filename)}`,
      {
        headers: {
          'X-Client-Location': location,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching file:', error);
    throw error;
  }
}

// -----------------------------
// FETCH NODES (REGISTRY)
// -----------------------------
export async function fetchNodes(): Promise<Node[]> {
  try {
    const response = await fetch(`${API.REGISTRY}/nodes`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching nodes:', error);
    throw error;
  }
}

// -----------------------------
// PURGE CACHE
// -----------------------------
export async function purgeFile(
  filename: string
): Promise<{ message: string; results?: any[] }> {
  try {
    const response = await fetch(`${API.PURGE}/purge`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ file: filename }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error purging file:', error);
    throw error;
  }
}

// -----------------------------
// MOCK DATA (OPTIONAL)
// -----------------------------
export const mockNodes: Node[] = [
  { id: 'edge-a', region: 'America', status: 'Healthy', latency: 20, capacity: 70 },
  { id: 'edge-b', region: 'Europe', status: 'Healthy', latency: 35, capacity: 80 },
  { id: 'edge-c', region: 'Asia', status: 'Healthy', latency: 50, capacity: 90 },
];

// -----------------------------
// REQUEST TIMELINE
// -----------------------------
export function createTimelineSteps(status: string): TimelineStep[] {
  const now = Date.now();

  const baseSteps: TimelineStep[] = [
    { stage: 'Request Created', timestamp: now, status: 'complete' },
    { stage: 'Traffic Manager Routing', timestamp: now + 50, status: 'complete' },
    { stage: 'Edge Node Selected', timestamp: now + 100, status: 'complete' },
  ];

  if (status === 'HIT') {
    return [
      ...baseSteps,
      { stage: 'Cache Hit', timestamp: now + 150, status: 'complete' },
      { stage: 'Response Sent', timestamp: now + 200, status: 'complete' },
    ];
  }

  if (status === 'MISS') {
    return [
      ...baseSteps,
      { stage: 'Cache Miss', timestamp: now + 150, status: 'complete' },
      { stage: 'Fetching from Origin', timestamp: now + 200, status: 'complete' },
      { stage: 'Response Sent', timestamp: now + 250, status: 'complete' },
    ];
  }

  if (status === 'BUSY') {
    return [
      ...baseSteps,
      { stage: 'Node Busy - Failover', timestamp: now + 150, status: 'complete' },
      { stage: 'Retrying on Another Node', timestamp: now + 200, status: 'complete' },
      { stage: 'Response Sent', timestamp: now + 250, status: 'complete' },
    ];
  }

  return baseSteps;
}