'use client';

import { useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Request, Node } from '@/lib/types';

interface VisualFlowDiagramProps {
  requests: Request[];
  nodes: Node[];
}

export function VisualFlowDiagram({ requests, nodes }: VisualFlowDiagramProps) {
  const canvasRef = useRef<SVGSVGElement>(null);

  const getNodeColor = (nodeId: string) => {
    const node = nodes.find((n) => n.id === nodeId);
    if (!node) return '#9ca3af';
    switch (node.status) {
      case 'Healthy':
        return '#10b981';
      case 'Busy':
        return '#f59e0b';
      case 'Down':
        return '#ef4444';
      default:
        return '#9ca3af';
    }
  };

  const getNodesByRegion = () => {
    return {
      Asia: nodes.filter((n) => n.region === 'Asia'),
      Europe: nodes.filter((n) => n.region === 'Europe'),
      America: nodes.filter((n) => n.region === 'America'),
    };
  };

  const nodesByRegion = getNodesByRegion();
  const maxNodesPerRegion = Math.max(
    nodesByRegion.Asia.length,
    nodesByRegion.Europe.length,
    nodesByRegion.America.length
  );

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-foreground">Network Architecture</CardTitle>
        <CardDescription className="text-muted-foreground">
          CDN request routing flow across regions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="w-full overflow-x-auto bg-secondary/20 rounded-lg p-4">
          <svg
            ref={canvasRef}
            viewBox="0 0 1200 300"
            className="min-w-full"
            style={{ height: '300px' }}
          >
            {/* Define gradients and markers */}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 10 3, 0 6" fill="#3b82f6" />
              </marker>
            </defs>

            {/* User */}
            <circle cx="50" cy="150" r="30" fill="#3b82f6" opacity="0.8" />
            <text x="50" y="155" textAnchor="middle" fill="#ffffff" fontSize="12" fontWeight="bold">
              User
            </text>

            {/* Traffic Manager */}
            <rect x="150" y="130" width="80" height="40" rx="4" fill="#06b6d4" opacity="0.8" />
            <text x="190" y="155" textAnchor="middle" fill="#000000" fontSize="11" fontWeight="bold">
              Traffic
            </text>
            <text x="190" y="168" textAnchor="middle" fill="#000000" fontSize="11" fontWeight="bold">
              Manager
            </text>

            {/* Arrows from User to Traffic Manager */}
            <line x1="80" y1="150" x2="150" y2="150" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />

            {/* Edge Nodes by Region */}
            {Object.entries(nodesByRegion).map(([region, regionNodes], regionIndex) => {
              const regionX = 320 + regionIndex * 220;
              const regionCenterY = 150;

              return (
                <g key={region}>
                  {/* Region label */}
                  <text x={regionX + 60} y="30" fill="#9ca3af" fontSize="12" fontWeight="bold">
                    {region} Nodes
                  </text>

                  {/* Region container */}
                  <rect
                    x={regionX - 10}
                    y={regionCenterY - 70}
                    width="140"
                    height="140"
                    rx="8"
                    fill="none"
                    stroke="#2d3748"
                    strokeWidth="2"
                    strokeDasharray="5,5"
                  />

                  {/* Nodes */}
                  {regionNodes.map((node, nodeIndex) => {
                    const nodeY = regionCenterY - 40 + (nodeIndex * 80) / Math.max(1, regionNodes.length - 1 || 1);
                    const nodeX = regionX + 60;

                    return (
                      <g key={node.id}>
                        {/* Node circle */}
                        <circle
                          cx={nodeX}
                          cy={nodeY}
                          r="20"
                          fill={getNodeColor(node.id)}
                          opacity="0.8"
                        />
                        {/* Status indicator dot */}
                        <circle
                          cx={nodeX + 12}
                          cy={nodeY - 12}
                          r="5"
                          fill={getNodeColor(node.id)}
                          stroke="#000000"
                          strokeWidth="1"
                        />
                        {/* Node label */}
                        <text
                          x={nodeX}
                          y={nodeY + 4}
                          textAnchor="middle"
                          fill="#ffffff"
                          fontSize="9"
                          fontWeight="bold"
                        >
                          {node.id.split('-')[2]}
                        </text>

                        {/* Arrow from Traffic Manager to node */}
                        <line
                          x1="230"
                          y1="150"
                          x2={nodeX - 20}
                          y2={nodeY}
                          stroke="#3b82f6"
                          strokeWidth="1"
                          opacity="0.3"
                          strokeDasharray="3,3"
                        />
                      </g>
                    );
                  })}
                </g>
              );
            })}

            {/* Origin Server */}
            <rect x="1070" y="130" width="80" height="40" rx="4" fill="#f59e0b" opacity="0.8" />
            <text x="1110" y="150" textAnchor="middle" fill="#000000" fontSize="11" fontWeight="bold">
              Origin
            </text>
            <text x="1110" y="163" textAnchor="middle" fill="#000000" fontSize="11" fontWeight="bold">
              Server
            </text>

            {/* Arrows from regions to origin */}
            {Object.entries(nodesByRegion).map(([_, regionNodes], regionIndex) => {
              const regionX = 380 + regionIndex * 220;
              return (
                <line
                  key={`arrow-${regionIndex}`}
                  x1={regionX + 50}
                  y1="150"
                  x2="1070"
                  y2="150"
                  stroke="#3b82f6"
                  strokeWidth="1"
                  opacity="0.3"
                  strokeDasharray="3,3"
                />
              );
            })}

            {/* Active request paths */}
            {requests.slice(0, 3).map((request, index) => {
              const regionIndex =
                request.location === 'Asia' ? 0 : request.location === 'Europe' ? 1 : 2;
              const regionX = 320 + regionIndex * 220;
              const offset = index * 8 - 8;

              return (
                <g key={`flow-${request.id}`} opacity="0.6">
                  <path
                    d={`M 80,${150 + offset} L 150,${150 + offset} L ${regionX + 40},${150 + offset} L ${1070},${150 + offset}`}
                    fill="none"
                    stroke={request.status === 'ERROR' ? '#ef4444' : '#3b82f6'}
                    strokeWidth="2"
                    opacity="0.5"
                  />
                </g>
              );
            })}

            {/* Legend */}
            <g>
              <text x="50" y="280" fill="#9ca3af" fontSize="10" fontWeight="bold">
                Legend:
              </text>
              <circle cx="110" cy="275" r="4" fill="#10b981" />
              <text x="120" y="280" fill="#9ca3af" fontSize="10">
                Healthy
              </text>
              <circle cx="190" cy="275" r="4" fill="#f59e0b" />
              <text x="200" y="280" fill="#9ca3af" fontSize="10">
                Busy
              </text>
              <circle cx="240" cy="275" r="4" fill="#ef4444" />
              <text x="250" y="280" fill="#9ca3af" fontSize="10">
                Down
              </text>
            </g>
          </svg>
        </div>
      </CardContent>
    </Card>
  );
}
