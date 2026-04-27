"use client";
import { useEffect } from 'react';

export default function Heartbeat() {
  useEffect(() => {
    // 5 minutes in milliseconds
    const PING_INTERVAL_MS = 5 * 60 * 1000; 

    const pingServer = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        await fetch(`${backendUrl}/api/health`, { method: 'GET', cache: 'no-store' });
        console.log('[Heartbeat] Ping sent to keep Render awake.');
      } catch (error) {
        console.warn('[Heartbeat] Ping failed:', error);
      }
    };

    // Delay the first ping slightly so it doesn't block initial page load
    setTimeout(pingServer, 10000);

    // Set interval for subsequent pings
    const interval = setInterval(pingServer, PING_INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  return null; // Invisible component
}
