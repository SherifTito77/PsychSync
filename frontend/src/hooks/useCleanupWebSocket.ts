/**
 * Memory-Safe WebSocket Hook
 * Provides WebSocket connection with automatic cleanup to prevent memory leaks
 *
 * @example
 * ```tsx
 * const ws = useWebSocket('ws://localhost:8000/ws', {
 *   onMessage: (data) => console.log('Received:', data),
 *   onError: (error) => console.error('Error:', error),
 *   onOpen: () => console.log('Connected'),
 *   onClose: () => console.log('Disconnected')
 * });
 *
 * // Send messages
 * ws.send(JSON.stringify({ type: 'ping' }));
 *
 * // Check connection status
 * if (ws.readyState === WebSocket.OPEN) {
 *   // Send data
 * }
 * ```
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface UseWebSocketOptions {
  onOpen?: (event: Event) => void;
  onMessage?: (data: any) => void;
  onError?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseWebSocketReturn {
  ws: WebSocket | null;
  readyState: number;
  send: (data: string | ArrayBuffer | Blob) => void;
  connect: () => void;
  disconnect: () => void;
  isConnected: boolean;
}

/**
 * useWebSocket - Memory-safe WebSocket connection with automatic cleanup
 *
 * @param url - WebSocket URL
 * @param options - Configuration options
 * @returns WebSocket control object
 */
export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    onOpen,
    onMessage,
    onError,
    onClose,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>();
  const reconnectAttemptsRef = useRef(0);

  const [readyState, setReadyState] = useState<number>(WebSocket.CLOSED);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const connect = useCallback(() => {
    // Don't connect if already connected or connecting
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      wsRef.current = new WebSocket(url);
      setReadyState(wsRef.current.readyState);

      ws.onopen = (event: Event) => {
        setReadyState(WebSocket.OPEN);
        setIsConnected(true);
        reconnectAttemptsRef.current = 0; // Reset reconnect attempts on successful connection
        onOpen?.(event);
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch {
          // If not JSON, send raw data
          onMessage?.(event.data);
        }
      };

      ws.onerror = (event: Event) => {
        setReadyState(ws.readyState);
        onError?.(event);
      };

      ws.onclose = (event: CloseEvent) => {
        setReadyState(WebSocket.CLOSED);
        setIsConnected(false);
        onClose?.(event);

        // Attempt reconnection if not closed cleanly and under max attempts
        if (!event.wasClean && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      onError?.(error as Event);
    }
  }, [url, onOpen, onMessage, onError, onClose, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setReadyState(WebSocket.CLOSED);
    setIsConnected(false);
  }, []);

  const send = useCallback((data: string | ArrayBuffer | Blob) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    } else {
      console.warn('[useWebSocket] Cannot send message, WebSocket is not connected');
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    // Cleanup function - close WebSocket on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    ws: wsRef.current,
    readyState,
    send,
    connect,
    disconnect,
    isConnected,
  };
}

/**
 * useWebSocketWithRef - WebSocket stored in useRef pattern (ESLint approved)
 *
 * @param url - WebSocket URL
 * @param options - Configuration options
 * @returns WebSocket control object with ref
 */
export function useWebSocketWithRef(
  url: string,
  options: UseWebSocketOptions = {}
): {
  wsRef: React.MutableRefObject<WebSocket | null>;
  send: (data: string | ArrayBuffer | Blob) => void;
  isConnected: boolean;
} {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      options.onOpen?.(ws);
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        options.onMessage?.(data);
      } catch {
        options.onMessage?.(event.data);
      }
    };

    ws.onerror = (event: Event) => {
      options.onError?.(event);
    };

    ws.onclose = () => {
      setIsConnected(false);
      options.onClose?.(ws as any);
    };

    // Cleanup function
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [url]);

  const send = useCallback((data: string | ArrayBuffer | Blob) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  return { wsRef, send, isConnected };
}

/**
 * ReadyState constants for convenience
 */
export const ReadyState = {
  CONNECTING: WebSocket.CONNECTING,
  OPEN: WebSocket.OPEN,
  CLOSING: WebSocket.CLOSING,
  CLOSED: WebSocket.CLOSED,
};
