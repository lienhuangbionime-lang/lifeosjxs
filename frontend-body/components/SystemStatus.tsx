// 檔案: frontend-body/components/SystemStatus.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { cortex, EvolutionStatus } from '@/lib/api/client';
import { Activity, RefreshCw, Zap, CheckCircle2, X } from 'lucide-react';

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
        <div className="fixed inset-0 z-[1] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in zoom-in duration-200">
          <div className="w-full max-w-sm bg-[#0f172a] border border-slate-700 rounded-2xl shadow-2xl overflow-hidden relative">
            
            {/* Modal Header */}
            <div className="bg-slate-900 p-4 border-b border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-2 text-slate-200 font-bold text-sm">
                    <Activity size={16} className="text-indigo-400"/>
                    System Status
                </div>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-500 hover:text-white">
                    <X size={18} />
                </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4">
                {/* 當前模型 */}
                <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                    <span className="text-slate-400 text-xs">Current Core</span>
                    <span className="font-mono text-xs text-emerald-400">{status.current_model}</span>
                </div>

                {/* 升級路徑 */}
                {isUpgradeAvailable ? (
                    <div className="flex justify-between items-center bg-amber-900/20 p-3 rounded-lg border border-amber-500/30">
                        <span className="text-amber-500/80 text-xs font-bold">New Version</span>
                        <div className="flex items-center gap-2">
                             <Zap size={12} className="text-amber-400" />
                             <span className="font-mono text-xs text-amber-400 font-bold">{status.recommended_upgrade}</span>
                        </div>
                    </div>
                ) : (
                   <div className="text-center py-2">
                      <p className="text-slate-600 text-xs">All systems operational. No updates found.</p>
                   </div>
                )}
                
                {/* 訊息顯示 */}
                {upgradeMessage && (
                    <div className="text-xs text-center text-emerald-400 font-mono bg-emerald-900/20 p-2 rounded">
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
                    <RefreshCw size={12}/> Refresh
                </button>
                
                {isUpgradeAvailable && (
                    <button 
                        onClick={handleUpgrade}
                        disabled={upgrading}
                        className="flex-1 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-500 flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/20 disabled:opacity-50"
                    >
                        {upgrading ? <RefreshCw className="animate-spin" size={14}/> : <Zap size={14}/>}
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