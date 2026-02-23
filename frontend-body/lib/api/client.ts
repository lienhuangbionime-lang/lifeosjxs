// frontend-body/lib/api/client.ts

// [Fix] Always use Next.js Proxy (Rewrite) to avoid CORS
export const API_BASE = "";

async function fetchJSON<T>(input: string, init?: RequestInit): Promise<T> {
  // Direct call through proxy
  const url = input.startsWith("/api/v1")
    ? input.replace(/^\/api\/v1/, "/api/py")
    : input;

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
  status: string;
  message?: string;
  model: string;
  data: {
    markdown_body: string;
    meta: {
      metrics: { mood: number; focus: number; energy: number };
      date?: string;
      tags?: string[];
      category?: string;
    };
    tasks: Array<{ title: string; status: string }>;
  };
}

/* --- Private Helper (神經傳導物質) --- */
// 自動處理 Rewrite 路徑與錯誤拋出
async function fetchProxy<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // [Critical] Always use Next.js Rewrite to avoid CORS
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
  async evolve(targetModel: string): Promise<{ success: boolean; message?: string }> {
    return await fetchProxy("/api/v1/system/upgrade", {
      method: "POST",
      body: JSON.stringify({ model: targetModel }),
    });
  },

  // 1. 檢查進化狀態 (System Status)
  async checkEvolution(): Promise<EvolutionStatus> {
    try {
      return await fetchProxy<EvolutionStatus>("/api/v1/system/status");
    } catch (e) {
      return {
        status: "offline",
        current_model: "Unknown",
        recommended_upgrade: null,
        note: "Cortex disconnected",
      };
    }
  },

  // 2. 發送確認升級指令 (Evolution Protocol)
  async confirmUpgrade(targetModel: string): Promise<{ success: boolean }> {
    return await fetchProxy("/api/v1/system/upgrade", {
      method: "POST",
      body: JSON.stringify({ model: targetModel }),
    });
  },

  // 2.5 獲取可用模型清單 (Dynamic Model List)
  async getAvailableModels(): Promise<{ models: Array<{ id: string; name: string; provider: string; is_free: boolean }> }> {
    try {
      return await fetchProxy("/api/v1/system/models");
    } catch (e) {
      console.warn("Model fetch failed, returning empty list.");
      return { models: [] };
    }
  },

  // [Fix] Alias for brain.generateGraph to support NeuralGraph.tsx
  async getBrainGraph(limit: number = 500): Promise<any> {
    return await this.brain.generateGraph(limit);
  },

  // 3. 記憶提取 (Memory Recall)
  async getRecentMemories(limit: number = 20, query?: string): Promise<LogEntry[]> {
    try {
      const qParam = query ? `&q=${encodeURIComponent(query)}` : "";
      return await fetchProxy<LogEntry[]>(`/api/v1/memories?limit=${limit}${qParam}`);
    } catch (e) {
      console.warn("Memory access failed, returning empty list.");
      return [];
    }
  },

  // 4. 感知輸入 (Sensory Ingest)
  async ingestLog(date: string, text: string): Promise<IngestResponse> {
    return await fetchProxy<IngestResponse>("/api/v1/ingest", {
      method: "POST",
      body: JSON.stringify({ date, text }),
    });
  },

  // [New] Knowledge Graph Support
  brain: {
    generateGraph: async (limit: number = 500): Promise<any> => {
      return await fetchProxy(`/api/v1/brain/graph?limit=${limit}`);
    },
    getContextualPrompts: async (): Promise<{ prompts: string[] }> => {
      return await fetchProxy<{ prompts: string[] }>("/api/v1/brain/contextual-prompts");
    },

    // [Phase B] AI Self-Reflection — Decision Logging
    growth: {
      logDecision: async (payload: {
        context: string;
        options: Record<string, string>;
        user_choice: string;
        ai_prediction: string;
        lessons?: string;
      }): Promise<{ status: string; prediction_match: boolean }> => {
        return await fetchProxy("/api/v1/brain/growth/log-decision", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      },
      getLessons: async (limit: number = 10): Promise<{
        lessons: any[];
        total: number;
        mismatch_rate_pct: number;
      }> => {
        return await fetchProxy(`/api/v1/brain/growth/lessons?limit=${limit}`);
      },
    },
  },


  async deleteNode(label: string): Promise<any> {
    return await fetchProxy(`/api/v1/brain/node/${encodeURIComponent(label)}`, {
      method: "DELETE",
    });
  },

  // [New] Ingest with Habits Support
  ingest: {
    submit: async (data: { content: string; habits: string[]; skipAi?: boolean; date?: string; mode?: 'overwrite' | 'append' }): Promise<IngestResponse> => {
      return await fetchProxy<IngestResponse>("/api/v1/ingest", {
        method: "POST",
        body: JSON.stringify({
          date: data.date || new Date().toLocaleDateString('en-CA'),
          content: data.content,
          habits: data.habits,
          skipAi: data.skipAi,
          mode: data.mode || 'append'
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
  },

  // 6. Prompt Management (大腦指引管理)
  async getPrompt(name: string): Promise<{ name: string; content: string; last_modified: string }> {
    return await fetchProxy(`/api/v1/system/prompts/${name}`);
  },

  async updatePrompt(name: string, content: string): Promise<any> {
    return await fetchProxy(`/api/v1/system/prompts/${name}`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  },

  // 7. 任務管理 (Task Management)
  async getTasks(projectId?: string): Promise<any[]> {
    const query = projectId ? `?project_id=${projectId}` : "";
    return await fetchProxy(`/api/v1/tasks/${query}`);
  },

  async completeTask(taskId: string): Promise<any> {
    return await fetchProxy(`/api/v1/tasks/${taskId}/complete`, {
      method: "POST",
    });
  }
};