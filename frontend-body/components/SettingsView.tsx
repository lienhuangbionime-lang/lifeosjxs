'use client';
import React from 'react';
import { Server, Activity, Database, Cpu } from 'lucide-react';

// [關鍵修正] 使用 export const (Named Export) 以配合 page.tsx 的引用
export const SettingsView = ({ logs = [], onImport }: { logs?: any[], onImport?: (data: any) => void }) => {
  return (
    <div className="h-full overflow-y-auto p-6 custom-scrollbar text-slate-300">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Server className="text-indigo-500" />
          System Configuration
        </h2>
        <p className="text-slate-500 text-sm mt-1">LifeOS v3.1 Autopoiesis 核心參數控制</p>
      </div>

      {/* 系統狀態面板 */}
      <div className="grid gap-4 mb-8">
        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
          <h3 className="text-xs font-bold text-slate-500 uppercase mb-4 tracking-wider">Neural Connection</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <div className="flex items-center gap-2">
                <Cpu size={14} className="text-emerald-500"/>
                <span>Cortex (FastAPI/Python)</span>
              </div>
              <span className="text-emerald-400 font-mono text-xs px-2 py-1 bg-emerald-500/10 rounded">● ACTIVE</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <div className="flex items-center gap-2">
                <Database size={14} className="text-blue-500"/>
                <span>Hippocampus (Supabase)</span>
              </div>
              <span className="text-blue-400 font-mono text-xs px-2 py-1 bg-blue-500/10 rounded">● CONNECTED</span>
            </div>
          </div>
        </div>

        {/* 簡單的資料顯示，證明組件運作中 */}
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-200 text-sm flex items-center gap-3">
          <Activity size={16} />
          <span>目前系統記憶庫中共有 {logs?.length || 0} 條神經節點。</span>
        </div>
      </div>
    </div>
  );
};
