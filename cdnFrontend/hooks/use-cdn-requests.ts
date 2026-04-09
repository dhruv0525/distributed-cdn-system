import { useState, useCallback } from 'react';
import { Request } from '@/lib/types';

export function useCDNRequests() {
  const [requests, setRequests] = useState<Request[]>([]);

  const addRequest = useCallback((request: Request) => {
    setRequests((prev) => [request, ...prev]);
  }, []);

  const updateRequest = useCallback((requestId: string, updates: Partial<Request>) => {
    setRequests((prev) =>
      prev.map((req) => (req.id === requestId ? { ...req, ...updates } : req))
    );
  }, []);

  const clearRequests = useCallback(() => {
    setRequests([]);
  }, []);

  return {
    requests,
    addRequest,
    updateRequest,
    clearRequests,
  };
}
