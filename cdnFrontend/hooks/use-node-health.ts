import { useState, useEffect, useCallback } from 'react';
import { Node } from '@/lib/types';
import { fetchNodes, mockNodes } from '@/lib/cdn-api';

export function useNodeHealth(pollingInterval: number = 3000) {
  const [nodes, setNodes] = useState<Node[]>(mockNodes);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchNodeData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchNodes();
      setNodes(data);
      setError(null);
    } catch (err) {
      // Use mock data if API call fails
      setNodes(mockNodes);
      console.log('Using mock node data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNodeData();

    // Poll for updates
    const interval = setInterval(fetchNodeData, pollingInterval);

    return () => clearInterval(interval);
  }, [fetchNodeData, pollingInterval]);

  return {
    nodes,
    loading,
    error,
    refetch: fetchNodeData,
  };
}
