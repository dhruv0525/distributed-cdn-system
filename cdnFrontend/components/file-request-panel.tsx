'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { fetchFile } from '@/lib/cdn-api';
import { Request } from '@/lib/types';

const REGIONS = ['Asia', 'Europe', 'America'];

interface FileRequestPanelProps {
  onRequestCreated: (request: Request) => void;
  onRequestUpdated: (requestId: string, updates: Partial<Request>) => void;
}

export function FileRequestPanel({ onRequestCreated, onRequestUpdated }: FileRequestPanelProps) {
  const [filename, setFilename] = useState('');
  const [location, setLocation] = useState('America');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRequest, setLastRequest] = useState<Request | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!filename.trim()) {
      setError('Please enter a filename');
      return;
    }

    setLoading(true);
    setError(null);

    const requestId = Math.random().toString(36).substring(7);
    const now = Date.now();

    try {
      const response = await fetchFile(filename, location);

      const request: Request = {
        id: requestId,
        filename,
        location,
        status: response.status || 'PENDING',
        selectedNode: response.selected_node || 'node-unknown',
        content: response.content,
        timestamp: now,
        timeline: [
          {
            stage: 'Request Created',
            timestamp: now,
            status: 'complete',
          },
        ],
        responseTime: response.latency,
      };

      setLastRequest(request);
      onRequestCreated(request);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);

      const request: Request = {
        id: requestId,
        filename,
        location,
        status: 'ERROR',
        selectedNode: 'unknown',
        timestamp: now,
        timeline: [
          {
            stage: 'Request Failed',
            timestamp: now,
            status: 'error',
            detail: errorMessage,
          },
        ],
      };

      setLastRequest(request);
      onRequestCreated(request);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-foreground">File Request</CardTitle>
        <CardDescription className="text-muted-foreground">
          Request a file from the CDN across different regions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Filename</label>
            <Input
              type="text"
              placeholder="e.g., index.html, app.js, styles.css"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              disabled={loading}
              className="bg-input border-border text-foreground placeholder:text-muted-foreground"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Region</label>
            <Select value={location} onValueChange={setLocation} disabled={loading}>
              <SelectTrigger className="bg-input border-border text-foreground">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-border bg-card">
                {REGIONS.map((region) => (
                  <SelectItem key={region} value={region} className="text-foreground">
                    {region}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {lastRequest && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="rounded-md bg-muted/20 p-3 space-y-2">
              <div className="text-xs font-medium text-foreground">Last Request:</div>
              <div className="text-xs text-muted-foreground space-y-1">
                <div>ID: <span className="font-mono text-accent">{lastRequest.id}</span></div>
                <div>Status: <span className={`font-semibold ${
                  lastRequest.status === 'HIT' ? 'text-green-400' :
                  lastRequest.status === 'MISS' ? 'text-amber-400' :
                  lastRequest.status === 'BUSY' ? 'text-blue-400' :
                  'text-destructive'
                }`}>{lastRequest.status}</span></div>
                <div>Node: <span className="font-mono">{lastRequest.selectedNode}</span></div>
                {lastRequest.responseTime && (
                  <div>Response Time: <span className="font-mono">{lastRequest.responseTime}ms</span></div>
                )}
              </div>
            </motion.div>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            {loading ? (
              <>
                <Spinner className="mr-2 h-4 w-4" />
                Fetching...
              </>
            ) : (
              'Fetch File'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
