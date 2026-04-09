export interface Request {
  id: string;
  filename: string;
  location: string;
  status: 'PENDING' | 'HIT' | 'MISS' | 'BUSY' | 'ERROR';
  selectedNode: string;
  content?: string;
  timestamp: number;
  timeline: TimelineStep[];
  path?: string[];
  responseTime?: number;
}

export interface Node {
  id: string;
  region: string;
  status: 'Healthy' | 'Busy' | 'Down';
  latency?: number;
  capacity?: number;
}

export interface TimelineStep {
  stage: string;
  timestamp: number;
  status: 'pending' | 'complete' | 'error';
  detail?: string;
}

export interface LoadSimulationResult {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  nodesUsed: string[];
  successRate: number;
}
