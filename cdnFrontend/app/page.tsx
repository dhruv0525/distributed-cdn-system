'use client';

import { motion } from 'framer-motion';
import { FileRequestPanel } from '@/components/file-request-panel';
import { NodeHealthDashboard } from '@/components/node-health-dashboard';
import { LiveLogsPanel } from '@/components/live-logs-panel';
import { VisualFlowDiagram } from '@/components/visual-flow-diagram';
import { RequestTimeline } from '@/components/request-timeline';
import { LoadSimulation } from '@/components/load-simulation';
import { useCDNRequests } from '@/hooks/use-cdn-requests';
import { useNodeHealth } from '@/hooks/use-node-health';

export default function Dashboard() {
  const { requests, addRequest, updateRequest, clearRequests } = useCDNRequests();
  const { nodes, loading: nodesLoading } = useNodeHealth();

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">CDN Dashboard</h1>
              <p className="text-muted-foreground mt-1">
                Distributed CDN System - Real-time Network Monitoring
              </p>
            </div>
            {requests.length > 0 && (
              <button
                onClick={clearRequests}
                className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground border border-border rounded-md hover:bg-secondary/50 transition-colors"
              >
                Clear Log
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Top row: File Request and Load Simulation */}
        <motion.div 
          className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div className="lg:col-span-2">
            <FileRequestPanel onRequestCreated={addRequest} onRequestUpdated={updateRequest} />
          </div>
          <div>
            <LoadSimulation onRequestCreated={addRequest} nodes={nodes} />
          </div>
        </motion.div>

        {/* Network Architecture */}
        <motion.div 
          className="mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <VisualFlowDiagram requests={requests} nodes={nodes} />
        </motion.div>

        {/* Node Health and Live Logs */}
        <motion.div 
          className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div>
            <NodeHealthDashboard nodes={nodes} loading={nodesLoading} />
          </div>
          <div className="h-full">
            <LiveLogsPanel requests={requests} onClearLogs={clearRequests} />
          </div>
        </motion.div>

        {/* Request Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <RequestTimeline requests={requests} />
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card/50 backdrop-blur-sm mt-8">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 text-center text-sm text-muted-foreground">
          <p>CDN Dashboard © 2024 - Built with Next.js & React</p>
        </div>
      </footer>
    </div>
  );
}
