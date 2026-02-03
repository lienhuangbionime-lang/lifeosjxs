'use client';

import React, { useState, useEffect } from 'react';
import { Cpu, RefreshCw, Zap } from 'lucide-react';

type EvolveReport = {
  current_model?: string;
  recommended_upgrade?: string | null;
  tested_candidates?: { model: string; passed: boolean; partial_compatibility?: boolean }[];
};

export const SystemStatus = () => {
  const [report, setReport] = useState<EvolveReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch('/api/py/system/evolve')
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`${res.status}`))))
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const hasUpgrade = report?.recommended_upgrade != null;
  const currentModel = report?.current_model ?? '—';

  const handleUpgrade = async () => {
    const target = report?.recommended_upgrade;
    if (!target) return;
    setUpgrading(true);
    try {
      const res = await fetch('/api/py/system/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_model: target }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.status === 'success') {
        setShowModal(false);
        setReport((prev) => (prev ? { ...prev, recommended_upgrade: null } : null));
      } else {
        alert(data.detail || data.error || '升級請求失敗');
      }
    } catch (e: any) {
      alert('連線失敗: ' + (e?.message || e));
    } finally {
      setUpgrading(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => hasUpgrade && setShowModal(true)}
        title={hasUpgrade ? `建議升級至 ${report?.recommended_upgrade}` : `目前模型: ${currentModel}`}
        className={`
          inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border transition-all
          ${hasUpgrade
            ? 'bg-amber-500/20 text-amber-400 border-amber-500/40 hover:bg-amber-500/30 animate-pulse'
            : 'bg-slate-800/80 text-emerald-400 border-slate-600 hover:bg-slate-700/80'
          }
        `}
      >
        {loading ? (
          <RefreshCw className="w-3 h-3 animate-spin" />
        ) : hasUpgrade ? (
          <>
            <span className="text-amber-400">🟠</span>
            <span>Evolution Available</span>
            <Zap className="w-3 h-3 text-amber-400" />
          </>
        ) : (
          <>
            <span>🟢</span>
            <span>System: Stable</span>
            <Cpu className="w-3 h-3 text-emerald-400/80" />
          </>
        )}
      </button>

      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-600 rounded-2xl shadow-2xl max-w-sm w-full p-6 text-slate-200">
            <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5 text-amber-400" />
              神經升級
            </h3>
            <p className="text-sm text-slate-400 mb-4">
              是否將模型升級至 <span className="font-mono text-indigo-300">{report?.recommended_upgrade}</span>？升級後需重啟 Cortex 才會生效。
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => !upgrading && setShowModal(false)}
                disabled={upgrading}
                className="flex-1 py-2.5 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-700 font-bold text-sm transition-colors disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={handleUpgrade}
                disabled={upgrading}
                className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {upgrading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    正在重組神經...
                  </>
                ) : (
                  '確認升級'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
