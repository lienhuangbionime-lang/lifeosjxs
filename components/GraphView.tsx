'use client';

import React, { useState } from 'react'; // [Add] useState
import { Activity } from 'lucide-react';
import { NeuralGraph } from '@/components/NeuralGraph';
import { ContextModal } from '@/components/ContextModal'; // [Add] Import Modal

export const GraphView = ({ logs }: { logs: any[] }) => {
    // [New] State for Modal
    const [selectedNode, setSelectedNode] = useState<any>(null);

    return (
        <div className="h-full flex flex-col">
            {/* Modal */}
            <ContextModal 
                mainNode={selectedNode} 
                logs={logs} 
                onClose={() => setSelectedNode(null)} 
            />

            <div className="flex-1 relative overflow-hidden rounded-2xl border border-slate-800 bg-[#0b1120]">
               <NeuralGraph 
                   logs={logs} 
                   onNodeClick={(node: any) => setSelectedNode(node)} // [Connect] Click Event
               />
            </div>
            <div className="p-4 text-center text-slate-500 text-xs">
               <Activity className="w-3 h-3 inline mr-1"/> 
               目前共有 {logs.length} 個節點正在運作
            </div>
        </div>
    );
};