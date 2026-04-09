'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Node } from '@/lib/types';

interface NodeHealthDashboardProps {
  nodes: Node[];
  loading: boolean;
}

export function NodeHealthDashboard({ nodes, loading }: NodeHealthDashboardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Healthy':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'Busy':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'Down':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'Healthy':
        return '●';
      case 'Busy':
        return '◐';
      case 'Down':
        return '○';
      default:
        return '◎';
    }
  };

  const groupedNodes = nodes.reduce(
    (acc, node) => {
      const region = node.region || 'Unknown';
      if (!acc[region]) {
        acc[region] = [];
      }
      acc[region].push(node);
      return acc;
    },
    {} as Record<string, Node[]>
  );

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-foreground">Node Health Status</CardTitle>
        <CardDescription className="text-muted-foreground">
          Real-time status of edge nodes across regions
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">Loading nodes...</div>
          </div>
        ) : Object.keys(groupedNodes).length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">No nodes available</div>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(groupedNodes).map(([region, regionNodes]) => (
              <div key={region} className="space-y-2">
                <h3 className="text-sm font-semibold text-foreground">{region}</h3>
                <motion.div className="space-y-2" variants={{
                  hidden: { opacity: 0 },
                  show: {
                    opacity: 1,
                    transition: {
                      staggerChildren: 0.05,
                    },
                  },
                }} initial="hidden" animate="show">
                  {regionNodes.map((node) => (
                    <motion.div variants={{
                      hidden: { opacity: 0, x: -10 },
                      show: { opacity: 1, x: 0 },
                    }}
                      key={node.id}
                      className="flex items-center justify-between p-3 rounded-md border border-border bg-secondary/30 hover:bg-secondary/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`text-lg leading-none font-bold ${
                            node.status === 'Healthy'
                              ? 'text-green-400'
                              : node.status === 'Busy'
                                ? 'text-amber-400'
                                : 'text-red-400'
                          }`}
                        >
                          {getStatusIndicator(node.status)}
                        </span>
                        <div>
                          <div className="text-sm font-medium text-foreground">{node.id}</div>
                          <div className="text-xs text-muted-foreground">{region}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {node.latency && (
                          <div className="text-right">
                            <div className="text-xs font-medium text-accent">{node.latency}ms</div>
                            <div className="text-xs text-muted-foreground">latency</div>
                          </div>
                        )}
                        <div
                          className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(node.status)}`}
                        >
                          {node.status}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
