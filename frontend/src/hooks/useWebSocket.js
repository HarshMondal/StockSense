import { useEffect, useRef, useState } from "react";

export function useWebSocket(url, { onMessage, shouldReconnect = true } = {}) {
  const socketRef = useRef();
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    if (!url) {
      return undefined;
    }

    let socket;
    let cancelled = false;

    function connect() {
      socket = new WebSocket(url);
      socketRef.current = socket;
      setStatus("connecting");

      socket.onopen = () => setStatus("open");
      socket.onclose = () => {
        setStatus("closed");
        if (shouldReconnect && !cancelled) {
          setTimeout(connect, 3000);
        }
      };
      socket.onerror = () => setStatus("error");
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          onMessage?.(payload, socket);
        } catch (error) {
          // eslint-disable-next-line no-console
          console.warn("Failed to parse websocket message", error);
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      socket?.close();
    };
  }, [url, onMessage, shouldReconnect]);

  return { socket: socketRef.current, status };
}
