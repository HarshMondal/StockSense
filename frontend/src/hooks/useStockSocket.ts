import { useEffect, useRef, useState } from 'react';
import type { Horizon, Tick } from '../types';

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:8000';
const MAX_POINTS = 120;

export type SocketStatus = 'connecting' | 'open' | 'closed' | 'unauthorized' | 'bad-horizon';

interface UseStockSocketResult {
  latest: Tick | null;
  ticks: Tick[];
  status: SocketStatus;
}

/**
 * Manages the prediction WebSocket lifecycle for a (ticker, horizon) pair.
 * - Reconnects with capped backoff on unexpected drops.
 * - Stops reconnecting on auth (4401) / bad-horizon (4400) closes.
 * - Cleans up fully on unmount or when ticker/horizon changes.
 */
export function useStockSocket(ticker: string, horizon: Horizon): UseStockSocketResult {
  const [latest, setLatest] = useState<Tick | null>(null);
  const [ticks, setTicks] = useState<Tick[]>([]);
  const [status, setStatus] = useState<SocketStatus>('connecting');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const stoppedRef = useRef(false);

  useEffect(() => {
    stoppedRef.current = false;
    attemptRef.current = 0;
    setLatest(null);
    setTicks([]);
    setStatus('connecting');

    const clearReconnect = () => {
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
        reconnectRef.current = null;
      }
    };

    const connect = () => {
      if (stoppedRef.current) return;
      setStatus('connecting');
      const url = `${WS_BASE}/ws/predictions/${encodeURIComponent(ticker)}/${horizon}/`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        attemptRef.current = 0;
        setStatus('open');
      };

      ws.onmessage = (event) => {
        let msg: unknown;
        try {
          msg = JSON.parse(event.data as string);
        } catch {
          return;
        }
        if (
          msg &&
          typeof msg === 'object' &&
          (msg as { type?: string }).type === 'tick'
        ) {
          const tick = msg as Tick;
          setLatest(tick);
          setTicks((prev) => {
            const next = [...prev, tick];
            return next.length > MAX_POINTS ? next.slice(next.length - MAX_POINTS) : next;
          });
        }
      };

      ws.onclose = (event) => {
        wsRef.current = null;
        if (stoppedRef.current) return;

        if (event.code === 4401) {
          setStatus('unauthorized');
          return;
        }
        if (event.code === 4400) {
          setStatus('bad-horizon');
          return;
        }

        setStatus('closed');
        const attempt = (attemptRef.current += 1);
        const delay = Math.min(1000 * 2 ** (attempt - 1), 15000);
        clearReconnect();
        reconnectRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        // onclose will follow and handle reconnect/backoff.
      };
    };

    connect();

    return () => {
      stoppedRef.current = true;
      clearReconnect();
      const ws = wsRef.current;
      wsRef.current = null;
      if (ws) {
        ws.onopen = null;
        ws.onmessage = null;
        ws.onclose = null;
        ws.onerror = null;
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close(1000, 'client-unmount');
        }
      }
    };
  }, [ticker, horizon]);

  return { latest, ticks, status };
}
