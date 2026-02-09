// frontend-body/lib/api/client.ts

export const API_BASE =
  (process.env.NEXT_PUBLIC_API_URL && process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "")) ||
  "http://localhost:8000";

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

// [Fix] 配合 SystemStatus.tsx 與 backend-cortex/app/api/v1/system.py
export interface EvolutionStatus {
  status: 'stable' | 'available' | 'offline';
  current_model: string;
  recommended_upgrade: string | null; // 這是 UI 判斷是否亮燈的關鍵
  model_versions?: string[]; // [New] Available model versions [fast, smart]
  remaining_requests?: string | null; // [New]
  note?: string;
}

// 配合 backend-cortex/app/models/domain.py
export interface LogEntry {
  id?: string;        // Supabase ID (UUID)
  date: string;       // YYYY-MM-DD
  content?: string | null; // Markdown content
  mood?: number | null;
  focus?: number | null;
  energy?: number | null;
  isAi?: boolean;     // 是否由 AI 生成
  aiModel?: string;   // 生成模型 (e.g., "gemini-2.0-flash")
  tags?: string[];    // [New] 支援標籤
}

// AI 分析的回傳結果 (配合 ingest.py 的回傳格式)
export interface IngestResponse {
  success: boolean;
  model: string;
  data: {
    markdown_body: string;
    meta: {
      metrics: { mood: number; focus: number; energy: number };
    };
    tasks: Array<{ title: string; status: string }>;
  };
}

/* --- Private Helper (神經傳導物質) --- */
// 自動處理 Rewrite 路徑與錯誤拋出
async function fetchProxy<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // [Critical] 強制將 /api/v1 轉為 /api/py 以觸發 next.config.js 的 Rewrite 規則
  // 這樣才能從 Vercel (Frontend) 穿透到 Render (Backend)
  const finalUrl = endpoint.replace(/^\/api\/v1/, "/api/py");

  try {
    const res = await fetch(finalUrl, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!res.ok) {
      // 嘗試讀取後端回傳的錯誤訊息
      const errorText = await res.text();
      throw new Error(`Cortex Error (${res.status}): ${errorText}`);
    }

    return await res.json();
  } catch (error: any) {
    console.error(`🔌 Neural Link Broken [${endpoint}]:`, error);
    throw error; // 讓 UI 層決定如何顯示錯誤
  }
}

/* --- Cortex API Client (大腦連線核心) --- */
export const cortex = {

  // [New] System Evolution (進化協定)
  // 對應後端: POST /api/v1/system/upgrade (需確認後端路由是否一致，假設為 upgrade)
  async evolve(targetModel: string): Promise<{ success: boolean; message?: string }> {
    return await fetchProxy("/api/v1/system/upgrade", {
      method: "POST",
      body: JSON.stringify({ model: targetModel }),
    });
  },

  // 1. 檢查進化狀態 (System Status)
  // 對應後端: GET /api/v1/system/status
  async checkEvolution(): Promise<EvolutionStatus> {
    try {
      // 使用 fetchProxy 自動處理路徑轉換
      return await fetchProxy<EvolutionStatus>("/api/v1/system/status");
    } catch (e) {
      // 如果連不上大腦，回傳預設的離線狀態 (防禦性編程)
      return {
        status: "offline",
        current_model: "Unknown",
        recommended_upgrade: null,
        note: "Cortex disconnected",
      };
    }
  },

  // 2. 發送確認升級指令 (Evolution Protocol)
  // 對應後端: POST /api/v1/system/upgrade
  async confirmUpgrade(targetModel: string): Promise<{ success: boolean }> {
    return await fetchProxy("/api/v1/system/upgrade", {
      method: "POST",
      body: JSON.stringify({ model: targetModel }),
    });
  },

  // 3. 記憶提取 (Memory Recall)
  // 對應後端: GET /api/v1/memories?limit=20
  async getRecentMemories(limit: number = 20): Promise<LogEntry[]> {
    try {
      return await fetchProxy<LogEntry[]>(`/api/v1/memories?limit=${limit}`);
    } catch (e) {
      console.warn("Memory access failed, returning empty list.");
      return [];
    }
  },

  // 4. 感知輸入 (Sensory Ingest)
  // 對應後端: POST /api/v1/ingest
  async ingestLog(date: string, text: string): Promise<IngestResponse> {
    return await fetchProxy<IngestResponse>("/api/v1/ingest", {
      method: "POST",
      body: JSON.stringify({ date, text }),
    });
  },

  // [New] Ingest with Habits Support
  ingest: {
    submit: async (data: { content: string; habits: string[]; skipAi?: boolean }): Promise<IngestResponse> => {
      return await fetchProxy<IngestResponse>("/api/v1/ingest", {
        method: "POST",
        body: JSON.stringify({
          date: new Date().toISOString().split('T')[0], // YYYY-MM-DD
          text: data.content,
          habits: data.habits,
          skip_ai: data.skipAi
        }),
      });
    }
  },

  // 5. 專案管理 (Project Management)
  async createProject(data: any): Promise<any> {
    return await fetchProxy("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateProject(id: number | string, data: any): Promise<any> {
    return await fetchProxy(`/api/v1/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteProject(id: number | string): Promise<any> {
    return await fetchProxy(`/api/v1/projects/${id}`, {
      method: "DELETE",
    });
  },

  async mergeProject(sourceId: number | string, targetId: number | string): Promise<any> {
    return await fetchProxy(`/api/v1/projects/${sourceId}/merge`, {
      method: "POST",
      body: JSON.stringify({ target_id: targetId }),
    });
  }
};