// 檔案位置: components/GraphView.tsx
'use client';

import React, { useState } from 'react';
import { Activity } from 'lucide-react';
import { NeuralGraph } from '@/frontend-body/components/NeuralGraph';
import { ContextModal } from '@/frontend-body/components/ContextModal'; // [New]

export const GraphView = ({ logs }: { logs: any[] }) => {
    const [contextNode, setContextNode] = useState(null);

    return (
        <div className="h-full flex flex-col">
            <ContextModal mainNode={contextNode} logs={logs} onClose={() => setContextNode(null)} />
            
            <div className="flex-1 relative overflow-hidden rounded-2xl border border-slate-800 bg-[#0b1120]">
               <NeuralGraph logs={logs} onNodeClick={setContextNode} />
            </div>
            <div className="p-4 text-center text-slate-500 text-xs">
               <Activity className="w-3 h-3 inline mr-1"/> 
               目前共有 {logs.length} 個節點正在運作
            </div>
        </div>
    );
};