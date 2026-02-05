'use client';

import React, { useState, useEffect } from 'react';
import { List, Calendar, AlertCircle, Loader2 } from 'lucide-react';

// 定義資料型別
interface LogEntry {
  id: string;
  date: string;
  note: string | null; // 注意：Supabase 表單通常是 note 或 content，請根據實際調整
  mood: number | null;
}

// 輔助函式：截斷過長的文字
const shortContent = (content: string, max: number) => {
  if (!content) return "";
  return content.length > max ? content.slice(0, max) + "…" : content;
}

// [Fix] 使用正確的箭頭函式語法 (export const Component = () => {})
export const HistoryView = () => {
  const [memories, setMemories] = useState<LogEntry[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMemories = async () => {
      try {
        setLoading(true);
        // [V3.1] 呼叫 Cortex (FastAPI) 的記憶端點
        // 透過 next.config.js 的 rewrite: /api/py/ -> http://localhost:8001/api/v1/
        const res = await fetch('/api/py/memories/daily?limit=30');
        
        if (!res.ok) {
            // 如果後端還沒準備好，使用 Mock Data 防止白屏
            console.warn("Cortex Offline, switching to local cache.");
            const saved = localStorage.getItem('life_os_logs_v8_0');
            if (saved) setMemories(JSON.parse(saved));
            else throw new Error("Cortex 連線失敗且無本地快取");
            return;
        }

        const data = await res.json();
        setMemories(data);
      } catch (err: any) {
        console.error("Recall Error:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMemories();
  }, []);

  return (
    <div className="h-full overflow-y-auto p-4 custom-scrollbar pb-24">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 border border-indigo-500/30">
           <List size={20}/>
        </div>
        <div>
           <h2 className="text-xl font-bold text-slate-100">Neural History</h2>
           <p className="text-slate-400 text-xs">海馬迴記憶庫 (Hippocampus)</p>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 text-slate-500 gap-2">
          <Loader2 className="animate-spin" size={24} />
          <span className="text-xs font-mono">Retrieving Memories...</span>
        </div>
      ) : error ? (
        <div className="p-4 bg-rose-950/30 border border-rose-500/30 rounded-xl flex items-center gap-3 text-rose-400">
          <AlertCircle size={20} />
          <span className="text-sm">記憶讀取錯誤: {error}</span>
        </div>
      ) : !memories || memories.length === 0 ? (
        <div className="py-12 text-center text-slate-600 border border-dashed border-slate-800 rounded-xl">
            <Calendar className="mx-auto mb-2 opacity-20" size={32}/>
            <p>尚無記憶痕跡</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {memories.map((m, idx) => (
            <li key={m.id || idx} className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 p-4 rounded-xl hover:bg-slate-800 hover:border-indigo-500/30 transition-all group">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-indigo-400 bg-indigo-950/30 px-2 py-0.5 rounded">
                        {m.date}
                      </span>
                  </div>
                  <div className="text-sm text-slate-300 leading-relaxed font-sans">
                    {shortContent(m.note || "(無內容)", 120)}
                  </div>
                </div>
                
                {/* 右側情緒指標 */}
                <div className="ml-4 flex flex-col items-end gap-1">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Mood</div>
                  <div className={`text-sm font-bold ${
                      (m.mood || 5) >= 7 ? 'text-emerald-400' : 
                      (m.mood || 5) <= 3 ? 'text-rose-400' : 'text-amber-400'
                  }`}>
                    {typeof m.mood === "number" ? m.mood : "—"}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};