"use client";
import React, { useEffect, useRef, useMemo, useState } from 'react';
import * as d3 from 'd3';
import { Activity } from 'lucide-react';

const NEON_PALETTE = {
    EMERALD: '#10b981', ROSE: '#f43f5e', BLUE: '#3b82f6', 
    INDIGO: '#6366f1', SLATE: '#475569', AMBER: '#f59e0b', PINK: '#ec4899'
};

export const NeuralGraph = ({ logs, onNodeClick }: { logs: any[], onNodeClick: (node: any) => void }) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [stats, setStats] = useState({ nodes: 0, links: 0 });

    // ... (此處完全貼上你原本 NeuralGraph 元件內的 useMemo 邏輯，處理 graphData) ...
    // 為節省篇幅，我將邏輯簡化描述：你需要保留 CoreEngine.parseGraphSeeds 的呼叫
    // 在 Next.js 中，我們可以把 CoreEngine 的邏輯抽取到 src/lib/utils.ts

    const graphData = useMemo(() => {
        if (!logs || logs.length === 0) return { nodes: [], links: [] };
        const nodesMap = new Map();
        const links: any[] = [];

        logs.forEach(log => {
            const id = new Date(log.date).toISOString().split('T')[0]; // Ensure string format
            // ... (貼上你的節點生成邏輯) ...
            // 範例：
            if (!nodesMap.has(id)) {
                 nodesMap.set(id, { id, group: 'date', val: 8, label: id.slice(5), color: NEON_PALETTE.INDIGO });
            }
        });
        return { nodes: Array.from(nodesMap.values()), links };
    }, [logs]);

    useEffect(() => {
        if (!graphData.nodes.length || !svgRef.current || !containerRef.current) return;
        const { clientWidth: width, clientHeight: height } = containerRef.current;
        
        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove();
        
        // ... (貼上你原本的 D3 forceSimulation, drag, zoom, drawing 邏輯) ...
        // 確保 simulation 的 force 參數與你提供的一致 (High Density)
        
    }, [graphData]);

    return (
        <div ref={containerRef} className="w-full h-[500px] bg-slate-900 rounded-3xl overflow-hidden relative border border-slate-800 shadow-2xl">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-1 pointer-events-none select-none">
                <div className="bg-slate-900/80 px-3 py-1 rounded-full text-xs text-emerald-400 font-mono flex items-center gap-2 border border-emerald-500/30 backdrop-blur">
                    <Activity size={12}/> Neon D3 Engine: ACTIVE
                </div>
            </div>
            <svg ref={svgRef} className="w-full h-full cursor-move"></svg>
        </div>
    );
};
