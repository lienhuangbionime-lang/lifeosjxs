// frontend-body/lib/api/client.ts

// 1. 讀取環境變數 (Vercel 上設定的那個)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const cortex = {
  // 健康檢查 (System Status 用)
  health: async () => {
    try {
      const res = await fetch(`${API_URL}/`);
      if (!res.ok) throw new Error('Cortex unreachable');
      return await res.json();
    } catch (e) {
      console.error('Brain disconnected:', e);
      return { status: 'offline', message: 'Cortex disconnected' };
    }
  },

  // 吞噬/輸入 (Capture View 用)
  ingest: async (content: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      return await res.json();
    } catch (e) {
      console.error('Ingest failed:', e);
      throw e;
    }
  },

  // 觸發進化 (Settings View 用)
  evolve: async () => {
    const res = await fetch(`${API_URL}/api/v1/system/upgrade`, { method: 'POST' });
    return await res.json();
  }
};