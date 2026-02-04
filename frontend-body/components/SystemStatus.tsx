// 檔案: frontend-body/components/SystemStatus.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { Activity, RefreshCw, Zap, CheckCircle2, WifiOff } from 'lucide-react';
import { cortex, type EvolutionStatus } from '@/lib/api/client'; // 👈 引入 Client

export const SystemStatus = () => {
  const [data, setData] = useState<EvolutionStatus | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  // 1. 檢查進化狀態 (改用 Client)
  const checkEvolution = async () => {
    const status = await cortex.checkEvolution();
    if (status.current_model === 'Offline') {
      setIsOffline(true);
    } else {
      setIsOffline(false);
      setData(status);
    }
  };

  useEffect(() => {
    checkEvolution();
    const timer = setInterval(checkEvolution, 60000); // 每分鐘輪詢
    return () => clearInterval(timer);
  }, []);

  // 2. 執行突變 (改用 Client)
  const handleUpgrade = async () => {
    if (!data?.recommended_upgrade) return;
    
    setIsMutating(true);
    try {
      // 呼叫 Client 執行進化
      await cortex.evolve(data.recommended_upgrade);
      
      setTimeout(() => {
        setIsMutating(false);
        setIsModalOpen(false);
        window.location.reload(); 
      }, 2000);
      
    } catch (e) {
      alert("進化失敗，Cortex 無回應");
      setIsMutating(false);
    }
  };

  // 離線狀態顯示
  if (isOffline) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-mono bg-rose-950/30 border-rose-500/50 text-rose-500 cursor-not-allowed">
        <WifiOff size={12} />
        <span>Cortex Offline</span>
      </div>
    );
  }

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
            ? 'bg-amber-950/30 border-amber-500/50 text-amber-400 hover:bg-amber-900/50 cursor-pointer animate-pulse shadow-[0_0_10px_rgba(245,158,11,0.2)]' 
            : 'bg-slate-900/50 border-emerald-500/30 text-emerald-500 cursor-default'}
        `}
      >
        <div className={`w-2 h-2 rounded-full ${data.recommended_upgrade ? 'bg-amber-500' : 'bg-emerald-500'}`} />
        {data.recommended_upgrade ? 'Evolution Available' : `v3.1 Stable`}
      </button>

      {/* --- Evolution Modal (保持您原本的設計) --- */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-sm bg-[#0f172a] border border-indigo-500/30 rounded-2xl shadow-2xl overflow-hidden relative animate-scale-in">
            {/* Header */}
            <div className="bg-slate-900 p-6 border-b border-slate-800 text-center relative overflow-hidden">
                <div className="absolute inset-0 bg-indigo-500/5 blur-3xl"></div>
                <div className="w-12 h-12 bg-indigo-900/30 rounded-full flex items-center justify-center mx-auto mb-4 border border-indigo-500/50 relative z-10">
                    <Zap className="text-indigo-400" size={24} />
                </div>
                <h3 className="text-lg font-bold text-white tracking-tight relative z-10">System Mutation</h3>
                <p className="text-slate-400 text-xs mt-1 relative z-10">偵測到更強大的認知模型</p>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
                <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                    <span className="text-slate-400 text-xs uppercase tracking-wider">Current DNA</span>
                    <span className="font-mono text-xs text-slate-300">{data.current_model}</span>
                </div>
                <div className="flex justify-center text-slate-600">
                    <Activity size={16} className="animate-bounce" />
                </div>
                <div className="flex justify-between items-center bg-indigo-900/20 p-3 rounded-lg border border-indigo-500/30">
                    <span className="text-indigo-300 text-xs font-bold uppercase tracking-wider">Target DNA</span>
                    <span className="font-mono text-xs text-amber-400 font-bold">{data.recommended_upgrade}</span>
                </div>
            </div>

            {/* Actions */}
            <div className="p-4 bg-slate-900 flex gap-3">
                <button 
                    onClick={() => setIsModalOpen(false)}
                    className="flex-1 py-2 rounded-xl border border-slate-700 text-slate-400 text-xs font-bold hover:bg-slate-800 transition-colors"
                >
                    Cancel
                </button>
                <button 
                    onClick={handleUpgrade}
                    disabled={isMutating}
                    className="flex-1 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-500 flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/20 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
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