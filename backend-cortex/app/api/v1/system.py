// 檔案: frontend-body/lib/api/client.ts

// [Config] 優先使用環境變數，開發時預設為後端 Port 8001 (注意：之前設定是 8001 或 8000，請確認 FastAPI 的 Port)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface EvolutionStatus {
  status: 'stable' | 'available';
  current_model: string;
  recommended_upgrade: string | null;
}

export const cortex = {
  // 1. 基本健康檢查
  health: async () => {
    try {
      const res = await fetch(`${API_URL}/`);
      return await res.json();
    } catch (e) {
      return { status: 'offline', message: 'Cortex disconnected' };
    }
  },

  // 2. [修正] 檢查進化狀態
  checkEvolution: async (): Promise<EvolutionStatus> => {
    try {
      // ⚠️ Fix: 後端定義為 /api/v1/system/evolve，非 /status
      const res = await fetch(`${API_URL}/api/v1/system/evolve`);
      if (!res.ok) throw new Error('Status check failed');
      return await res.json();
    } catch (e) {
      console.error("Cortex Link Error:", e);
      // Fallback: 回傳安全預設值，防止 UI 白屏
      return { status: 'stable', current_model: 'Connection Lost', recommended_upgrade: null };
    }
  },

  // 3. 執行進化
  evolve: async (targetModel: string) => {
    const res = await fetch(`${API_URL}/api/v1/system/upgrade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_model: targetModel }),
    });
    if (!res.ok) throw new Error('Evolution failed');
    return await res.json();
  },

  // 4. 輸入日記 (Ingest)
  ingest: async (content: string) => {
    const res = await fetch(`${API_URL}/api/v1/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    return await res.json();
  }
};
