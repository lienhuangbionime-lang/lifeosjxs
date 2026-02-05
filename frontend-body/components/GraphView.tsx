// 檔案: frontend-body/components/GraphView.tsx
'use client';
import React, { useState } from 'react';
import dynamic from 'next/dynamic'; // [Fix] 動態載入
import { Activity } from 'lucide-react';
import { ContextModal } from '@/components/ContextModal';
import { cortex } from "@/lib/api/client";

// [Fix] 強制關閉 SSR，解決 "window is not defined" 或 Hydration 錯誤
const NeuralGraph = dynamic(
  () => import('@/components/NeuralGraph').then((mod) => mod.NeuralGraph),
  { ssr: false, loading: () => <div className="text-slate-500 text-xs p-4">載入神經網路中...</div> }
);

export const GraphView = ({ logs }: { logs: any[] }) => {
  const [contextNode, setContextNode] = useState(null);

  // [Fix] 防禦性檢查：確保 logs 是陣列
  const safeLogs = Array.isArray(logs) ? logs : [];

  return (
    <div className="h-full flex flex-col">
      <ContextModal mainNode={contextNode} logs={safeLogs} onClose={() => setContextNode(null)} />
      
      <div className="flex-1 relative overflow-hidden rounded-2xl border border-slate-800 bg-[#0b1120] shadow-inner">
        {/* 傳入處理過的安全資料 */}
        <NeuralGraph logs={safeLogs} onNodeClick={setContextNode} />
      </div>
      
      <div className="p-4 text-center text-slate-500 text-xs font-mono">
        <Activity className="w-3 h-3 inline mr-1 text-indigo-500"/> 
        Active Nodes: {safeLogs.length}
      </div>
    </div>
  );
};