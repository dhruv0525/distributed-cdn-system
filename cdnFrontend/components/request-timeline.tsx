'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Request, TimelineStep } from '@/lib/types';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useState } from 'react';

interface RequestTimelineProps {
  requests: Request[];
}

export function RequestTimeline({ requests }: RequestTimelineProps) {
  const [selectedRequest, setSelectedRequest] = useState<Request | null>(null);

  const latestRequest = requests[0];

  if (!latestRequest) {
    return (
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-foreground">Request Timeline</CardTitle>
          <CardDescription className="text-muted-foreground">
            Lifecycle of the most recent request
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            No requests yet. Make a request to see the timeline.
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStepColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'text-green-400';
      case 'pending':
        return 'text-amber-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-muted-foreground';
    }
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return '✓';
      case 'pending':
        return '○';
      case 'error':
        return '✕';
      default:
        return '—';
    }
  };

  return (
    <>
      <Card className="border-border bg-card cursor-pointer hover:bg-secondary/20 transition-colors" onClick={() => setSelectedRequest(latestRequest)}>
        <CardHeader>
          <CardTitle className="text-foreground">Request Timeline</CardTitle>
          <CardDescription className="text-muted-foreground">
            Lifecycle of the most recent request
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Request header */}
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-border">
              <div>
                <div className="text-sm font-medium text-foreground">{latestRequest.filename}</div>
                <div className="text-xs text-muted-foreground">{latestRequest.location}</div>
              </div>
              <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                latestRequest.status === 'HIT' ? 'bg-green-500/20 text-green-400' :
                latestRequest.status === 'MISS' ? 'bg-amber-500/20 text-amber-400' :
                latestRequest.status === 'BUSY' ? 'bg-blue-500/20 text-blue-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {latestRequest.status}
              </div>
            </div>

            {/* Timeline steps */}
            <motion.div className="space-y-3" variants={{
              hidden: { opacity: 0 },
              show: {
                opacity: 1,
                transition: {
                  staggerChildren: 0.1,
                },
              },
            }} initial="hidden" animate="show">
              {latestRequest.timeline.map((step, index) => (
                <motion.div key={index} className="flex gap-4 items-start" variants={{
                  hidden: { opacity: 0, x: -10 },
                  show: { opacity: 1, x: 0 },
                }}>
                  {/* Timeline node */}
                  <div className="flex flex-col items-center">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      step.status === 'complete' ? 'bg-green-500/20 text-green-400 border border-green-500/50' :
                      step.status === 'pending' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50' :
                      'bg-red-500/20 text-red-400 border border-red-500/50'
                    }`}>
                      {getStepIcon(step.status)}
                    </div>
                    {index < latestRequest.timeline.length - 1 && (
                      <div className="w-0.5 h-8 bg-gradient-to-b from-border to-transparent my-1" />
                    )}
                  </div>

                  {/* Step content */}
                  <div className="flex-1 py-1">
                    <div className="text-sm font-medium text-foreground">{step.stage}</div>
                    {step.detail && (
                      <div className="text-xs text-muted-foreground">{step.detail}</div>
                    )}
                    <div className="text-xs text-muted-foreground mt-1">
                      {new Date(step.timestamp).toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false,
                      })}
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>

            <div className="text-xs text-muted-foreground text-center pt-2">
              Click to see full details
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detail dialog */}
      <Dialog open={!!selectedRequest} onOpenChange={() => setSelectedRequest(null)}>
        <DialogContent className="border-border bg-card max-h-96 overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-foreground">Request Details</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Complete lifecycle information
            </DialogDescription>
          </DialogHeader>

          {selectedRequest && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Request ID</div>
                  <div className="text-sm font-mono text-accent">{selectedRequest.id}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Status</div>
                  <div className={`text-sm font-semibold ${
                    selectedRequest.status === 'HIT' ? 'text-green-400' :
                    selectedRequest.status === 'MISS' ? 'text-amber-400' :
                    selectedRequest.status === 'BUSY' ? 'text-blue-400' :
                    'text-red-400'
                  }`}>{selectedRequest.status}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Filename</div>
                  <div className="text-sm text-foreground">{selectedRequest.filename}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Region</div>
                  <div className="text-sm text-foreground">{selectedRequest.location}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Selected Node</div>
                  <div className="text-sm font-mono text-accent">{selectedRequest.selectedNode}</div>
                </div>
                {selectedRequest.responseTime && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground uppercase">Response Time</div>
                    <div className="text-sm text-foreground">{selectedRequest.responseTime}ms</div>
                  </div>
                )}
              </div>

              <div>
                <div className="text-xs font-semibold text-muted-foreground uppercase mb-3">Timeline</div>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {selectedRequest.timeline.map((step, index) => (
                    <div key={index} className="flex gap-3 items-start p-2 rounded bg-secondary/20">
                      <span className={`text-xs font-bold min-w-fit ${getStepColor(step.status)}`}>
                        {getStepIcon(step.status)}
                      </span>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-foreground">{step.stage}</div>
                        {step.detail && (
                          <div className="text-xs text-muted-foreground">{step.detail}</div>
                        )}
                        <div className="text-xs text-muted-foreground mt-1">
                          {new Date(step.timestamp).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            hour12: false,
                          })}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {selectedRequest.content && (
                <div>
                  <div className="text-xs font-semibold text-muted-foreground uppercase mb-2">Content Preview</div>
                  <div className="p-2 rounded bg-secondary/20 text-xs text-foreground font-mono max-h-32 overflow-y-auto">
                    {selectedRequest.content.substring(0, 200)}
                    {selectedRequest.content.length > 200 && '...'}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
