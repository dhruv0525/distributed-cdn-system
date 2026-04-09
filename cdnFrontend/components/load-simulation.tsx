'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { fetchFile, createTimelineSteps, mockNodes } from '@/lib/cdn-api';
import { Request, LoadSimulationResult } from '@/lib/types';

const REGIONS = ['Asia', 'Europe', 'America'];
const TEST_FILES = ['index.html', 'app.js', 'styles.css', 'logo.png', 'data.json'];

interface LoadSimulationProps {
  onRequestCreated: (request: Request) => void;
  nodes: any[];
}

export function LoadSimulation({ onRequestCreated, nodes }: LoadSimulationProps) {
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState<LoadSimulationResult | null>(null);
  const [requestCount, setRequestCount] = useState(5);

  const handleSimulate = async () => {
    setSimulating(true);
    setResult(null);

    const requests: Request[] = [];
    const startTime = Date.now();
    let successCount = 0;
    const nodesUsed = new Set<string>();
    const responseTimes: number[] = [];

    try {
      // Create parallel requests with staggered timing for visibility
      const promises = Array.from({ length: requestCount }, (_, i) => {
        return new Promise<void>((resolve) => {
          setTimeout(async () => {
            const filename = TEST_FILES[i % TEST_FILES.length];
            const location = REGIONS[i % REGIONS.length];
            const requestId = Math.random().toString(36).substring(7);
            const now = Date.now();

            try {
              const response = await fetchFile(filename, location);
              successCount++;
              responseTimes.push(response.latency || 100);
              nodesUsed.add(response.selected_node);

              const request: Request = {
                id: requestId,
                filename,
                location,
                status: response.status || 'PENDING',
                selectedNode: response.selected_node,
                content: response.content,
                timestamp: now,
                timeline: createTimelineSteps(response.status),
                responseTime: response.latency,
              };

              requests.push(request);
              onRequestCreated(request);
            } catch (error) {
              const request: Request = {
                id: requestId,
                filename,
                location,
                status: 'ERROR',
                selectedNode: 'unknown',
                timestamp: now,
                timeline: createTimelineSteps('ERROR'),
              };

              requests.push(request);
              onRequestCreated(request);
            }

            resolve();
          }, i * 200); // Stagger requests by 200ms for visibility
        });
      });

      await Promise.all(promises);

      const endTime = Date.now();
      const avgResponseTime =
        responseTimes.length > 0
          ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
          : 0;

      setResult({
        totalRequests: requestCount,
        successfulRequests: successCount,
        failedRequests: requestCount - successCount,
        averageResponseTime: avgResponseTime,
        nodesUsed: Array.from(nodesUsed),
        successRate: (successCount / requestCount) * 100,
      });
    } finally {
      setSimulating(false);
    }
  };

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-foreground">Load Simulation</CardTitle>
        <CardDescription className="text-muted-foreground">
          Send parallel requests to test CDN performance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Number of Requests: <span className="text-accent">{requestCount}</span>
          </label>
          <input
            type="range"
            min="1"
            max="20"
            value={requestCount}
            onChange={(e) => setRequestCount(Number(e.target.value))}
            disabled={simulating}
            className="w-full"
          />
        </div>

        <Button
          onClick={handleSimulate}
          disabled={simulating}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          {simulating ? (
            <>
              <Spinner className="mr-2 h-4 w-4" />
              Simulating...
            </>
          ) : (
            'Simulate Load'
          )}
        </Button>

        {result && (
          <motion.div 
            className="space-y-3 p-4 rounded-lg bg-secondary/20 border border-border"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="text-sm font-semibold text-foreground">Simulation Results</div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1 p-2 rounded bg-secondary/30">
                <div className="text-xs text-muted-foreground">Total Requests</div>
                <div className="text-lg font-bold text-accent">{result.totalRequests}</div>
              </div>
              <div className="space-y-1 p-2 rounded bg-secondary/30">
                <div className="text-xs text-muted-foreground">Success Rate</div>
                <div className={`text-lg font-bold ${result.successRate === 100 ? 'text-green-400' : 'text-amber-400'}`}>
                  {result.successRate.toFixed(0)}%
                </div>
              </div>
              <div className="space-y-1 p-2 rounded bg-secondary/30">
                <div className="text-xs text-muted-foreground">Successful</div>
                <div className="text-lg font-bold text-green-400">{result.successfulRequests}</div>
              </div>
              <div className="space-y-1 p-2 rounded bg-secondary/30">
                <div className="text-xs text-muted-foreground">Avg Response Time</div>
                <div className="text-lg font-bold text-accent">{result.averageResponseTime}ms</div>
              </div>
            </div>

            {result.nodesUsed.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-muted-foreground">Nodes Used</div>
                <div className="flex flex-wrap gap-2">
                  {result.nodesUsed.map((nodeId) => (
                    <span key={nodeId} className="px-2 py-1 rounded text-xs bg-primary/20 text-primary border border-primary/30">
                      {nodeId}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}
