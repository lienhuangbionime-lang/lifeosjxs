// 檔案: frontend-body/components/SystemStatus.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { Activity, RefreshCw, Zap, AlertCircle, CheckCircle2 } from 'lucide-react';

interface EvolutionStatus {
  status: 'stable' | 'available';
  current_model: string;
  recommended_upgrade: string | null;
}

export const SystemStatus = () => {
  const [data, setData] = useState<EvolutionStatus | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMutating, setIsMutating] = useState(false);

  // 1. 檢查進化狀態
  const checkEvolution = async () => {
    try {
      const res = await fetch('/api/py/system/evolve');
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error("Evolution check failed:", e);
    }
  };

  useEffect(() => {
    checkEvolution();
    // 可選：每 60 秒輪詢一次
    const timer = setInterval(checkEvolution, 60000);
    return () => clearInterval(timer);
  }, []);

  // 2. 執行突變
  const handleUpgrade = async () => {
    if (!data?.recommended_upgrade) return;
    
    setIsMutating(true);
    try {
      const res = await fetch('/api/py/system/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_model: data.recommended_upgrade }),
      });
      
      if (!res.ok) throw new Error('Mutation failed');
      
      // 成功後延遲一下，讓使用者看到動畫，然後重整頁面
      setTimeout(() => {
        setIsMutating(false);
        setIsModalOpen(false);
        window.location.reload(); // 重新載入以獲取新狀態
      }, 2000);
      
    } catch (e) {
      alert("進化失敗，請檢查 Console");
      setIsMutating(false);
    }
  };

  if (!data) return null;

  return (
    <>
      {/* --- Status Pill Button --- */}
      <button
        onClick={() => data.recommended_upgrade && setIsModalOpen(true)}
        disabled={!data.recommended_upgrade}
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-mono transition-all duration-300
          ${data.recommended_upgrade 
            ? 'bg-amber-950/30 border-amber-500/50 text-amber-400 hover:bg-amber-900/50 cursor-pointer animate-pulse' 
            : 'bg-slate-900/50 border-emerald-500/30 text-emerald-500 cursor-default'}
        `}
      >
        <div className={`w-2 h-2 rounded-full ${data.recommended_upgrade ? 'bg-amber-500' : 'bg-emerald-500'}`} />
        {data.recommended_upgrade ? 'Evolution Available' : 'System Stable'}
      </button>

      {/* --- Evolution Modal --- */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[1] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-scale-in">
          <div className="w-full max-w-sm bg-[#0f172a] border border-indigo-500/30 rounded-2xl shadow-2xl overflow-hidden relative">
            {/* Header */}
            <div className="bg-slate-900 p-6 border-b border-slate-800 text-center">
                <div className="w-12 h-12 bg-indigo-900/30 rounded-full flex items-center justify-center mx-auto mb-4 border border-indigo-500/50">
                    <Zap className="text-indigo-400" size={24} />
                </div>
                <h3 className="text-lg font-bold text-white tracking-tight">System Mutation</h3>
                <p className="text-slate-400 text-xs mt-1">偵測到更強大的認知模型</p>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
                <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                    <span className="text-slate-400 text-xs">Current</span>
                    <span className="font-mono text-xs text-slate-300">{data.current_model}</span>
                </div>
                <div className="flex justify-center text-slate-500">
                    <Activity size={16} />
                </div>
                <div className="flex justify-between items-center bg-indigo-900/20 p-3 rounded-lg border border-indigo-500/30">
                    <span className="text-indigo-300 text-xs font-bold">Target</span>
                    <span className="font-mono text-xs text-amber-400 font-bold">{data.recommended_upgrade}</span>
                </div>
            </div>

            {/* Actions */}
            <div className="p-4 bg-slate-900 flex gap-3">
                <button 
                    onClick={() => setIsModalOpen(false)}
                    className="flex-1 py-2 rounded-xl border border-slate-700 text-slate-400 text-xs font-bold hover:bg-slate-800"
                >
                    Cancel
                </button>
                <button 
                    onClick={handleUpgrade}
                    disabled={isMutating}
                    className="flex-1 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-500 flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/20"
                >
                    {isMutating ? <RefreshCw className="animate-spin" size={14}/> : <CheckCircle2 size={14}/>}
                    {isMutating ? 'Mutating...' : 'Confirm Upgrade'}
                </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};