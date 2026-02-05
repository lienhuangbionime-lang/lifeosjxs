// frontend-body/components/HistoryView.tsx
"use client";

import React, { useEffect, useState } from "react";
import { cortex, LogEntry } from "@/lib/api/client";

function shortContent(content?: string | null, max = 120) {
  if (!content) return "";
  return content.length > max ? content.slice(0, max) + "…" : content;
}

export default function HistoryView(): JSX.Element {
  const [memories, setMemories] = useState<LogEntry[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    cortex
      .getMemories(50)
      .then((data) => {
        if (!mounted) return;
        setMemories(data ?? []);
      })
      .catch((err: Error) => {
        if (!mounted) return;
        setError(err.message || "無法讀取記憶");
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="p-4 rounded-md bg-white dark:bg-slate-800 shadow-sm">
      <h3 className="text-lg font-semibold mb-3">歷史回溯</h3>

      {loading ? (
        <p className="text-sm text-gray-500">讀取中…</p>
      ) : error ? (
        <p className="text-sm text-red-500">錯誤: {error}</p>
      ) : !memories || memories.length === 0 ? (
        <div className="py-8 text-center text-gray-500">尚無記憶</div>
      ) : (
        <ul className="space-y-3">
          {memories.map((m) => (
            <li key={m.id ?? m.date} className="p-3 border rounded hover:bg-gray-50 dark:hover:bg-slate-700">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-sm text-gray-500">
                    {new Date(m.date).toLocaleString()}
                  </div>
                  <div className="mt-1 text-sm text-slate-700 dark:text-slate-200">
                    {shortContent(m.content ?? "(無內容)", 180)}
                  </div>
                </div>
                <div className="ml-4 text-right">
                  <div className="text-xs text-gray-500">Mood</div>
                  <div className="text-sm font-medium">{typeof m.mood === "number" ? m.mood : "—"}</div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}