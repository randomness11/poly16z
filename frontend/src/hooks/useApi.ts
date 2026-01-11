import { useState, useEffect, useCallback } from 'react';
import type {
  StatusResponse,
  PerformanceResponse,
  ExposureResponse,
  ArbitrageResponse,
  Position,
  Trade,
} from '../types/api';

const API_BASE = '/api';

async function fetchJson<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

async function postJson<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, { method: 'POST' });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export function useStatus(refreshInterval = 5000) {
  const [data, setData] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const status = await fetchJson<StatusResponse>('/status');
      setData(status);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval]);

  return { data, error, loading, refresh };
}

export function usePerformance(refreshInterval = 10000) {
  const [data, setData] = useState<PerformanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const perf = await fetchJson<PerformanceResponse>('/performance');
      setData(perf);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval]);

  return { data, error, loading, refresh };
}

export function useExposure(refreshInterval = 30000) {
  const [data, setData] = useState<ExposureResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const exposure = await fetchJson<ExposureResponse>('/exposure');
      setData(exposure);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval]);

  return { data, error, loading, refresh };
}

export function usePositions(refreshInterval = 10000) {
  const [data, setData] = useState<Position[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const positions = await fetchJson<Position[]>('/positions');
      setData(positions);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval]);

  return { data, error, loading, refresh };
}

export function useTrades(limit = 50) {
  const [data, setData] = useState<Trade[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const trades = await fetchJson<Trade[]>(`/trades?limit=${limit}`);
      setData(trades);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, error, loading, refresh };
}

export function useArbitrage() {
  const [data, setData] = useState<ArbitrageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);

  const fetch_cached = useCallback(async () => {
    try {
      setLoading(true);
      const arb = await fetchJson<ArbitrageResponse>('/arbitrage');
      setData(arb);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  const scan = useCallback(async () => {
    try {
      setScanning(true);
      const arb = await postJson<ArbitrageResponse>('/arbitrage/scan');
      setData(arb);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setScanning(false);
    }
  }, []);

  useEffect(() => {
    fetch_cached();
  }, [fetch_cached]);

  return { data, error, loading, scanning, scan, refresh: fetch_cached };
}

export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<unknown>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch {
        // Ignore parse errors
      }
    };

    return () => ws.close();
  }, []);

  return { connected, lastMessage };
}

export function useAgentControl() {
  const [loading, setLoading] = useState(false);

  const start = useCallback(async () => {
    setLoading(true);
    try {
      await postJson('/control/start');
    } finally {
      setLoading(false);
    }
  }, []);

  const stop = useCallback(async () => {
    setLoading(true);
    try {
      await postJson('/control/stop');
    } finally {
      setLoading(false);
    }
  }, []);

  const setDryRun = useCallback(async (enabled: boolean) => {
    setLoading(true);
    try {
      await postJson(`/control/dry-run/${enabled}`);
    } finally {
      setLoading(false);
    }
  }, []);

  return { start, stop, setDryRun, loading };
}
