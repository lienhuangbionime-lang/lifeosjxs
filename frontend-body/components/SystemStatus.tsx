// 檔案: frontend-body/components/SystemStatus.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { cortex, EvolutionStatus } from '@/lib/api/client';
import { Activity, RefreshCw, Zap, CheckCircle2, X, Brain } from 'lucide-react';

// [Fix 1] 使用具名匯出 (Named Export) 以匹配 page.tsx 的 import { SystemStatus }
export const SystemStatus = () => {
  const [status, setStatus] = useState<EvolutionStatus | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  const [upgradeMessage, setUpgradeMessage] = useState<string | null>(null);

  // 1. 初始化檢查
  const checkHealth = async () => {
    try {
      const res = await cortex.checkEvolution();
      setStatus(res);
    } catch (e) {
      console.error("Cortex disconnect", e);
    }
  };

  useEffect(() => {
    checkHealth();
    // 建立每 60 秒的心跳檢查
    const timer = setInterval(checkHealth, 60000);
    return () => clearInterval(timer);
  }, []);

  // 2. 觸發進化
  const handleUpgrade = async () => {
    if (!status?.recommended_upgrade) return;

    setUpgrading(true);
    setUpgradeMessage(null);
    try {
      // 呼叫後端進化接口
      const res = await cortex.evolve(status.recommended_upgrade);
      setUpgradeMessage(res.message ?? "Evolution triggered.");

      // 成功後重新整理頁面以載入新配置
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (e: any) {
      setUpgradeMessage(e?.message ?? "Upgrade failed");
      setUpgrading(false);
    }
  };

  // 如果連線失敗或還沒載入，暫時不顯示
  if (!status) return null;

  // 判斷是否可升級
  const isUpgradeAvailable = status.status === 'available' || !!status.recommended_upgrade;

  return (
    <>
      {/* --- [UI Part 1] Header 上的膠囊按鈕 (Pill) --- */}
      <button
        onClick={() => setIsModalOpen(true)}
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-full border text-[10px] font-mono transition-all duration-300
          ${isUpgradeAvailable
            ? 'bg-amber-950/30 border-amber-500/50 text-amber-400 hover:bg-amber-900/50 animate-pulse cursor-pointer'
            : 'bg-slate-900/50 border-emerald-500/30 text-emerald-500 hover:bg-slate-800 cursor-pointer'}
        `}
      >
        <div className={`w-1.5 h-1.5 rounded-full ${isUpgradeAvailable ? 'bg-amber-500' : 'bg-emerald-500'}`} />
        {isUpgradeAvailable ? 'EVOLUTION AVAILABLE' : 'SYSTEM STABLE'}
      </button>

      {/* --- [UI Part 2] 點擊後彈出的詳細資訊 (Modal) --- */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[50] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in zoom-in duration-200">
          <div className="w-full max-w-md bg-[#0f172a] border border-slate-700 rounded-2xl shadow-2xl overflow-hidden relative">

            {/* Modal Header */}
            <div className="bg-slate-900 p-4 border-b border-slate-800 flex justify-between items-center">
              <div className="flex items-center gap-2 text-slate-200 font-bold text-sm">
                <Activity size={16} className="text-indigo-400" />
                System Status
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-500 hover:text-white">
                <X size={18} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-5">
              {/* 當前模型 */}
              <div className="flex flex-col gap-2 bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-xs font-medium uppercase tracking-wider">Current Core</span>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="font-mono text-xs text-emerald-400 font-bold">{status.current_model}</span>
                  </div>
                </div>
                {/* [New] 剩餘額度 - Failed checks often return null, handle gracefully */}
                <div className="mt-2 pt-2 border-t border-slate-700/50 flex justify-between items-center">
                  <span className="text-slate-500 text-xs">Daily Token Usage</span>
                  <span className="font-mono text-xs text-blue-400">
                    {status.remaining_requests ?? "Unknown"}
                  </span>
                </div>
              </div>

              {/* 升級路徑 */}
              {isUpgradeAvailable ? (
                <div className="flex flex-col gap-3 p-4 bg-amber-950/10 rounded-xl border border-amber-900/30">
                  <span className="text-amber-500/80 text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                    <Zap size={12} /> Evolution Available
                  </span>
                  <div className="flex justify-between items-center bg-black/20 p-2 rounded-lg">
                    <span className="text-slate-400 text-xs">Target Version</span>
                    <span className="font-mono text-xs text-amber-400 font-bold">{status.recommended_upgrade}</span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-1 flex flex-col gap-3">
                  {/* Show available models list if present */}
                  {(status as any).model_versions && (status as any).model_versions.length > 0 && (
                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800 text-left">
                      <p className="text-[10px] text-slate-500 mb-3 font-bold uppercase tracking-wider flex items-center gap-2">
                        <Brain size={12} /> Registered Models
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {(status as any).model_versions.map((m: string, idx: number) => (
                          <span key={`${m}-${idx}`} className={`text-[11px] px-2.5 py-1 rounded-md border transition-colors ${m === status.current_model ? 'bg-emerald-950/30 text-emerald-400 border-emerald-800/50 shadow-sm shadow-emerald-900/20' : 'bg-slate-800/80 text-slate-400 border-slate-700/80 hover:border-slate-600'}`}>
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <p className="text-[10px] text-slate-600 italic">System operating within normal parameters.</p>
                </div>
              )}

              {/* 訊息顯示 */}
              {upgradeMessage && (
                <div className="text-xs text-center text-emerald-400 font-mono bg-emerald-950/30 border border-emerald-900/50 p-2.5 rounded-lg">
                  {upgradeMessage}
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="p-4 bg-slate-900 flex gap-3">
              <button
                onClick={checkHealth}
                className="flex-1 py-2 rounded-xl border border-slate-700 text-slate-400 text-xs font-bold hover:bg-slate-800 flex justify-center items-center gap-2"
              >
                <RefreshCw size={12} /> Refresh
              </button>

              {isUpgradeAvailable && (
                <button
                  onClick={handleUpgrade}
                  disabled={upgrading}
                  className="flex-1 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-500 flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/20 disabled:opacity-50"
                >
                  {upgrading ? <RefreshCw className="animate-spin" size={14} /> : <Zap size={14} />}
                  {upgrading ? 'Mutating...' : 'Evolve Now'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};