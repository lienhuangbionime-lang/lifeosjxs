// frontend-body/components/SystemStatus.tsx
"use client";

import React, { useEffect, useState } from "react";
import { cortex, SystemStatus } from "@/lib/api/client";

export default function SystemStatusCard(): JSX.Element {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [upgrading, setUpgrading] = useState<boolean>(false);
  const [upgradeMessage, setUpgradeMessage] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    cortex
      .checkEvolution()
      .then((res) => {
        if (!mounted) return;
        setStatus(res);
      })
      .catch((err: Error) => {
        if (!mounted) return;
        setError(err.message || "無法取得系統狀態");
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const handleUpgrade = async () => {
    setUpgrading(true);
    setUpgradeMessage(null);
    try {
      // you can pass a target model string if desired
      const res = await cortex.evolve();
      setUpgradeMessage(res.message ?? "Evolution triggered.");
      // refresh status after upgrade trigger
      try {
        const refreshed = await cortex.checkEvolution();
        setStatus(refreshed);
      } catch {
        // ignore refresh error
      }
    } catch (e: any) {
      setUpgradeMessage(e?.message ?? "Upgrade failed");
    } finally {
      setUpgrading(false);
    }
  };

  return (
    <div className="p-4 rounded-md shadow-md bg-white dark:bg-slate-800">
      <h3 className="text-lg font-semibold mb-2">系統進化狀態</h3>

      {loading ? (
        <p className="text-sm text-gray-500">讀取中…</p>
      ) : error ? (
        <p className="text-sm text-red-500">錯誤: {error}</p>
      ) : status ? (
        <>
          <div className="mb-3">
            <p className="text-sm text-gray-600">
              狀態: <span className="font-medium">{status.status}</span>
            </p>
            <p className="text-sm text-gray-600">
              目前模型: <span className="font-medium">{status.current_model}</span>
            </p>
            <p className="text-sm text-gray-600">
              可用版本:
              <span className="ml-2 text-sm text-slate-700 dark:text-slate-300">
                {status.model_versions.join(" , ")}
              </span>
            </p>
            {status.note && <p className="text-xs text-gray-500 mt-1">說明: {status.note}</p>}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleUpgrade}
              disabled={upgrading}
              className="px-3 py-1 rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {upgrading ? "觸發中…" : "觸發進化"}
            </button>

            <button
              onClick={async () => {
                setLoading(true);
                setError(null);
                try {
                  const refreshed = await cortex.checkEvolution();
                  setStatus(refreshed);
                } catch (err: any) {
                  setError(err?.message ?? "刷新失敗");
                } finally {
                  setLoading(false);
                }
              }}
              className="px-3 py-1 rounded border text-sm"
            >
              刷新
            </button>
          </div>

          {upgradeMessage && <p className="text-sm text-green-600 mt-2">{upgradeMessage}</p>}
        </>
      ) : (
        <p className="text-sm text-gray-500">沒有可用狀態資料</p>
      )}
    </div>
  );
}