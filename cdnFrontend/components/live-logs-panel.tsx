'use client';

import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Request } from '@/lib/types';
import { Button } from '@/components/ui/button';

interface LogEntry {
  id: string;
  timestamp: number;
  type: 'request' | 'status' | 'error' | 'cache' | 'failover';
  message: string;
  details?: string;
}

interface LiveLogsPanelProps {
  requests: Request[];
  onClearLogs?: () => void;
}

export function LiveLogsPanel({ requests, onClearLogs }: LiveLogsPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const generateLogs = (): LogEntry[] => {
    const logs: LogEntry[] = [];

    requests.forEach((request) => {
      // Add request log
      logs.push({
        id: `${request.id}-request`,
        timestamp: request.timestamp,
        type: 'request',
        message: `File request created`,
        details: `${request.filename} from ${request.location}`,
      });

      // Add status log
      const statusType =
        request.status === 'HIT'
          ? 'cache'
          : request.status === 'MISS'
            ? 'cache'
            : request.status === 'BUSY'
              ? 'failover'
              : 'error';

      logs.push({
        id: `${request.id}-status`,
        timestamp: request.timestamp + 100,
        type: statusType,
        message: `Cache ${request.status === 'HIT' ? 'HIT' : request.status === 'MISS' ? 'MISS' : request.status === 'BUSY' ? 'BUSY - Failover' : 'ERROR'}`,
        details: `Node: ${request.selectedNode}`,
      });
    });

    return logs.sort((a, b) => b.timestamp - a.timestamp);
  };

  const logs = generateLogs();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColor = (type: string) => {
    switch (type) {
      case 'cache':
        return 'text-green-400 bg-green-400/10';
      case 'failover':
        return 'text-amber-400 bg-amber-400/10';
      case 'error':
        return 'text-red-400 bg-red-400/10';
      case 'request':
        return 'text-blue-400 bg-blue-400/10';
      default:
        return 'text-gray-400 bg-gray-400/10';
    }
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  return (
    <Card className="border-border bg-card flex flex-col h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-foreground">Live Activity Log</CardTitle>
            <CardDescription className="text-muted-foreground">
              Real-time system events and request tracking
            </CardDescription>
          </div>
          {onClearLogs && logs.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={onClearLogs}
              className="border-border text-foreground hover:bg-secondary"
            >
              Clear
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden">
        <div
          ref={scrollRef}
          className="h-full overflow-y-auto space-y-2 pr-4 text-sm font-mono"
        >
          {logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              No activity yet. Make a request to see logs.
            </div>
          ) : (
            logs.map((log, index) => (
              <motion.div 
                key={log.id} 
                className="py-1 space-y-1"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: Math.min(index * 0.05, 0.3) }}
              >
                <div className="flex gap-3 items-start">
                  <span className="text-muted-foreground min-w-fit">[{formatTime(log.timestamp)}]</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold min-w-fit ${getLogColor(log.type)}`}>
                    {log.type.toUpperCase()}
                  </span>
                  <span className="text-foreground flex-1">{log.message}</span>
                </div>
                {log.details && (
                  <div className="flex gap-3 items-start pl-3">
                    <span className="text-muted-foreground min-w-fit">→</span>
                    <span className="text-muted-foreground text-xs flex-1">{log.details}</span>
                  </div>
                )}
              </motion.div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
