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
  
  // 處理 204 No Content 或空回應
  const text = await res.text();
  const data = text ? JSON.parse(text) : undefined;

  if (!res.ok) {
    const msg = data && typeof data === "object" && (data as any).message ? (data as any).message : res.statusText;
    throw new Error(msg || `Request failed: ${res.status}`);
  }

  return data as T;
}

/* --- TypeScript Interfaces (定義資料結構) --- */

// [Fix] 這裡改名為 EvolutionStatus 以匹配 SystemStatus.tsx 的需求
// 同時補上 recommended_upgrade 欄位，讓 UI 的進化按鈕能正常運作
export interface EvolutionStatus {
  status: 'stable' | 'available' | 'offline';
  current_model: string;
  recommended_upgrade: string | null; // 這是 UI 判斷是否亮燈的關鍵
  note?: string;
}

export interface LogEntry {
  id?: string; // Supabase ID 是 UUID (string)
  date: string; // ISO string
  content?: string | null;
  mood?: number | null;
  focus?: number | null;
  energy?: number | null;
  isAi?: boolean;
  aiModel?: string;
}

/* --- Cortex API Client (大腦連線核心) --- */
export const cortex = {
  // 1. 檢查進化狀態
  async checkEvolution(): Promise<EvolutionStatus> {
    try {
      return await fetchJSON<EvolutionStatus>("/api/v1/system/status", {
        method: "GET",
      });
    } catch (e) {
      // 離線保護機制：如果後端沒開，回傳離線狀態，避免前端白屏
      return {
        status: 'offline',
        current_model: 'Disconnect',
        recommended_upgrade: null
      };
    }
  },

  // 2. 執行進化 (升級模型)
  async evolve(targetModel: string): Promise<{ success: boolean; message?: string }> {
    return fetchJSON<{ success: boolean; message?: string }>("/api/v1/system/upgrade", {
      method: "POST",
      body: JSON.stringify({ target_model: targetModel }),
    });
  },

  // 3. 讀取記憶 (HistoryView 用)
  async getMemories(limit = 50): Promise<LogEntry[]> {
    try {
      const res = await fetchJSON<{ data: LogEntry[] }>(`/api/v1/memories?limit=${encodeURIComponent(String(limit))}`, {
        method: "GET",
      });
      return res.data || [];
    } catch (e) {
      console.error("Failed to fetch memories:", e);
      return [];
    }
  },

  // 4. 感知輸入 (CaptureView 用)
  async ingest(text: string, meta?: Partial<Pick<LogEntry, "mood" | "focus" | "energy">>): Promise<LogEntry> {
    // 取得當地的 YYYY-MM-DD
    const today = new Date().toISOString().split('T')[0];
    
    const payload = {
      text: text,
      date: today, // 確保符合後端 IngestRequest 格式
      ...meta,
    };

    const res = await fetchJSON<{ success: boolean; data: any }>("/api/v1/ingest", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    
    return res.data; 
  },
};