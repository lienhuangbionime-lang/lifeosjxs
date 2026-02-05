'use client';

import React, { useState } from 'react';
import { Activity } from 'lucide-react';
import dynamic from 'next/dynamic'; // [Fix] 必須引入 dynamic
import { ContextModal } from '@/components/ContextModal';
import { cortex } from "@/lib/api/client"; 

// [Fix] 移除原本的靜態 import: import { NeuralGraph } from '@/components/NeuralGraph';
// 改用 dynamic import 來解決 D3 在 Next.js SSR 的 "window is not defined" 問題
const NeuralGraph = dynamic(
  () => import('@/components/NeuralGraph').then((mod) => mod.NeuralGraph),
  { 
    ssr: false, 
    loading: () => <div className="text-slate-500 text-xs p-4 flex items-center gap-2"><Activity className="animate-spin" size={12}/> 載入神經網路中...</div> 
  }
);

export const GraphView = ({ logs }: { logs?: any[] }) => {
  const [contextNode, setContextNode] = useState(null);
  
  // 容錯處理：如果 logs 為 undefined，給予空陣列
  const displayLogs = logs || [];

  return (
    <div className="h-full flex flex-col">
      <ContextModal mainNode={contextNode} logs={displayLogs} onClose={() => setContextNode(null)} />
      
      <div className="flex-1 relative overflow-hidden rounded-2xl border border-slate-800 bg-[#0b1120]">
        <NeuralGraph logs={displayLogs} onNodeClick={setContextNode} />
      </div>
      
      <div className="p-4 text-center text-slate-500 text-xs font-mono">
        <Activity className="w-3 h-3 inline mr-1 text-indigo-500"/>
        NEURAL ACTIVITY: {displayLogs.length} NODES
      </div>
    </div>
  );
};