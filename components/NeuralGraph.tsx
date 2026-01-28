// 檔案位置: components/NeuralGraph.tsx
'use client';

import React, { useEffect, useRef, memo, useState } from 'react';
import * as d3 from 'd3';
import { Activity, Layers, LayoutGrid } from 'lucide-react';
import { NEON_PALETTE, CoreEngine } from '@/lib/ai/core';

interface LogNode extends d3.SimulationNodeDatum {
  id: string;
  val: number;
  label: string;
  color: string;
  group?: string;
  raw?: any;
  isSignal?: boolean;
  x?: number;
  y?: number;
}

interface LogLink extends d3.SimulationLinkDatum<LogNode> {
  type: string;
  tag?: string;
}

export const NeuralGraph = memo(({ logs, onNodeClick }: { logs: any[], onNodeClick: (n:any)=>void }) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [mode, setMode] = useState('gravity');
    const [stats, setStats] = useState({ nodes: 0, links: 0 });
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

    useEffect(() => {
        if (!containerRef.current) return;
        const resizeObserver = new ResizeObserver((entries) => {
            if (!entries || entries.length === 0) return;
            const { width, height } = entries[0].contentRect;
            if (width > 0 && height > 0) {
                setDimensions({ width, height });
            }
        });
        resizeObserver.observe(containerRef.current);
        return () => resizeObserver.disconnect();
    }, []);

    useEffect(() => {
        // 🔴 關鍵修正：捕捉當下的 ref，避免 cleanup 時 ref 已經變 null
        const svgElement = svgRef.current;
        if (!logs || logs.length === 0 || !svgElement || dimensions.width === 0) return;
        
        const { width, height } = dimensions;
        let simulation: d3.Simulation<LogNode, LogLink> | null = null;

        try {
            // Data Processing
            const nodesMap = new Map<string, LogNode>();
            const links: LogLink[] = [];

            logs.forEach(log => {
                const id = log.date;
                const noteContent = typeof log.note === 'string' ? log.note : '';
                const graphContent = log.graphSeeds?.content || '';
                const seeds = CoreEngine ? CoreEngine.parseGraphSeeds(noteContent, graphContent) : { tags: [], links: [] };
                
                if (!nodesMap.has(id)) {
                    const mood = Number(log.metrics?.mood || 5);
                    const focus = Number(log.metrics?.focus || 5);
                    let color = NEON_PALETTE.INDIGO;
                    if (log.isSignal) color = NEON_PALETTE.BLUE;
                    else if (mood > 7) color = NEON_PALETTE.EMERALD;
                    else if (mood < 4) color = NEON_PALETTE.ROSE;

                    nodesMap.set(id, { 
                        id, val: 10 + (focus * 1.5), label: id.slice(5), color, raw: log,
                        x: width/2 + (Math.random()-0.5)*10, y: height/2 + (Math.random()-0.5)*10
                    });
                }
                seeds.tags.forEach((tag: string) => {
                    if(!nodesMap.has(tag)) nodesMap.set(tag, { id: tag, val: 8, label: tag, color: NEON_PALETTE.PINK, group: 'tag', x:width/2, y:height/2 });
                    links.push({ source: id, target: tag, type: 'tag' });
                });
            });

            const nodes = Array.from(nodesMap.values());
            setStats({ nodes: nodes.length, links: links.length });

            // D3 Rendering
            const svg = d3.select(svgElement);
            svg.selectAll("*").remove(); // Clear previous render

            const g = svg.append("g");
            
            simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id((d:any) => d.id).distance(60))
                .force("charge", d3.forceManyBody().strength(mode === 'cluster' ? -50 : -120))
                .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))
                .force("collide", d3.forceCollide().radius((d:any) => d.val + 4).iterations(2));

            const link = g.append("g").selectAll("line").data(links).join("line")
                .attr("stroke", "#6366f1").attr("stroke-opacity", 0.2).attr("stroke-width", 1);

            const node = g.append("g").selectAll("g").data(nodes).join("g")
                .call(d3.drag<any, any>()
                    .on("start", (e, d) => { if (!e.active) simulation?.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
                    .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
                    .on("end", (e, d) => { if (!e.active) simulation?.alphaTarget(0); d.fx = null; d.fy = null; })
                )
                .on("click", (e, d) => { e.stopPropagation(); onNodeClick(d.raw || d); });

            node.append("circle").attr("r", (d:any) => d.val).attr("fill", (d:any) => d.color).attr("stroke", "#1e293b").attr("stroke-width", 2);
            node.append("text").text((d:any) => d.label).attr("text-anchor", "middle").attr("dy", (d:any) => d.val + 12).attr("fill", "#94a3b8").attr("font-size", "10px").style("pointer-events", "none");

            simulation.on("tick", () => {
                link.attr("x1", (d:any) => d.source.x).attr("y1", (d:any) => d.source.y).attr("x2", (d:any) => d.target.x).attr("y2", (d:any) => d.target.y);
                node.attr("transform", (d:any) => `translate(${d.x},${d.y})`);
            });

        } catch (error) {
            console.error("D3 Error:", error);
        }

        // 🔴 關鍵修正：Cleanup Function (防止崩潰的主因)
        // 當組件卸載 (Unmount) 時，強制停止 D3 運算
        return () => {
            if (simulation) simulation.stop();
            if (svgElement) {
                d3.select(svgElement).selectAll("*").remove();
            }
        };

    }, [logs, mode, dimensions, onNodeClick]);

    return (
        <div ref={containerRef} className="w-full h-[500px] bg-[#0b1120] rounded-3xl overflow-hidden relative border border-slate-800 shadow-2xl">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-2 pointer-events-none">
                <div className="bg-slate-900/80 px-3 py-1 rounded-full text-xs text-emerald-400 font-mono flex items-center gap-2 border border-emerald-500/30 backdrop-blur">
                    <Activity size={12}/> Neon D3 Engine: ACTIVE
                </div>
            </div>
            <div className="absolute top-4 right-4 z-20 flex gap-2">
                <button onClick={() => setMode('gravity')} className={`p-2 rounded-lg border transition-all ${mode==='gravity'?'bg-indigo-600 border-indigo-400 text-white':'bg-slate-800 border-slate-700 text-slate-400'}`}><Layers size={16}/></button>
                <button onClick={() => setMode('cluster')} className={`p-2 rounded-lg border transition-all ${mode==='cluster'?'bg-indigo-600 border-indigo-400 text-white':'bg-slate-800 border-slate-700 text-slate-400'}`}><LayoutGrid size={16}/></button>
            </div>
            <svg ref={svgRef} className="w-full h-full cursor-move block"></svg>
        </div>
    );
});
// 🔴 關鍵修正：加入 DisplayName 讓 Vercel 不要報錯
NeuralGraph.displayName = "NeuralGraph";