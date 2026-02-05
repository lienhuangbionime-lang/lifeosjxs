// frontend-body/lib/api/client.ts
export const API_BASE =
  (process.env.NEXT_PUBLIC_API_URL && process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "")) ||
  "http://localhost:8001";

async function fetchJSON<T>(input: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${input}`;
  const headers = {
    "Content-Type": "application/json",
    ...(init && (init.headers as Record<string, string>)),
  };

  const res = await fetch(url, { ...init, headers });
  const text = await res.text();
  // attempt parse if body exists
  const data = text ? JSON.parse(text) : undefined;

  if (!res.ok) {
    // try to get message from server JSON
    const msg = data && typeof data === "object" && (data as any).message ? (data as any).message : res.statusText;
    throw new Error(msg || `Request failed: ${res.status}`);
  }

  return data as T;
}

/* TypeScript interfaces */
export interface SystemStatus {
  status: "ok" | "degraded" | "offline";
  current_model: string;
  model_versions: string[];
  note?: string;
}

export interface LogEntry {
  id?: number;
  date: string; // ISO string
  content?: string | null;
  mood?: number | null;
  focus?: number | null;
  energy?: number | null;
}

/* cortex API client */
export const cortex = {
  async checkEvolution(): Promise<SystemStatus> {
    return fetchJSON<SystemStatus>("/api/v1/system/status", {
      method: "GET",
    });
  },

  /**
   * Trigger an evolve/upgrade action.
   * backend simulates action; targetModel is optional metadata.
   */
  async evolve(targetModel?: string): Promise<{ success: boolean; message?: string }> {
    const body = targetModel ? { targetModel } : {};
    return fetchJSON<{ success: boolean; message?: string }>("/api/v1/system/upgrade", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async getMemories(limit = 50): Promise<LogEntry[]> {
    // backend GET /api/v1/memories returns an array of LogEntry
    // If you need to pass query params for limit later, append ?limit=...
    return fetchJSON<LogEntry[]>(`/api/v1/memories?limit=${encodeURIComponent(String(limit))}`, {
      method: "GET",
    });
  },

  async ingest(text: string, meta?: Partial<Pick<LogEntry, "mood" | "focus" | "energy">>): Promise<LogEntry> {
    const payload: Partial<LogEntry> = {
      date: new Date().toISOString(),
      content: text,
      ...meta,
    };

    return fetchJSON<LogEntry>("/api/v1/ingest", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};