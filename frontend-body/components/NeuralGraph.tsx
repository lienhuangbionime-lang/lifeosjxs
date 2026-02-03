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

// [Fix 1] 命名元件函式，而不是使用匿名函式
const NeuralGraphComponent = ({ logs, onNodeClick }: { logs: any[], onNodeClick: (n:any)=>void }) => {
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
        if (!logs || logs.length === 0 || !svgRef.current || dimensions.width === 0) return;
        
        // [Fix 2] 捕捉目前的 ref 值，確保 cleanup 時能正確存取
        const currentSvgRef = svgRef.current;
        const { width, height } = dimensions;
        let simulation: d3.Simulation<LogNode, LogLink> | null = null;

        try {
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
                        id, 
                        val: 10 + (focus * 1.5),
                        label: id.slice(5), 
                        color, 
                        raw: log,
                        x: width / 2 + (Math.random() - 0.5) * 50,
                        y: height / 2 + (Math.random() - 0.5) * 50
                    });
                }
                
                seeds.tags.forEach((tag: string) => {
                    if(!nodesMap.has(tag)) {
                        nodesMap.set(tag, { 
                            id: tag, 
                            val: 8, 
                            label: tag, 
                            color: NEON_PALETTE.PINK, 
                            group: 'tag',
                            x: width / 2,
                            y: height / 2
                        });
                    }
                    links.push({ source: id, target: tag, type: 'tag' });
                });

                seeds.links.forEach((target: string) => {
                      if (!nodesMap.has(target)) {
                          nodesMap.set(target, {
                              id: target,
                              val: 5,
                              label: target,
                              color: NEON_PALETTE.SLATE,
                              group: 'stub',
                              x: width / 2,
                              y: height / 2
                          });
                      }
                      links.push({ source: id, target: target, type: 'manual' });
                });
            });

            const nodes = Array.from(nodesMap.values());
            setStats(prev => (prev.nodes === nodes.length ? prev : { nodes: nodes.length, links: links.length }));

            const svg = d3.select(currentSvgRef);
            svg.selectAll("*").remove();

            const g = svg.append("g");
            
            simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id((d:any) => d.id).distance(60))
                .force("charge", d3.forceManyBody().strength(mode === 'cluster' ? -50 : -120))
                .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))
                .force("collide", d3.forceCollide().radius((d:any) => d.val + 4).iterations(2));

            const link = g.append("g")
                .selectAll("line")
                .data(links)
                .join("line")
                .attr("stroke", "#6366f1")
                .attr("stroke-opacity", 0.2)
                .attr("stroke-width", (d:any) => d.type === 'manual' ? 1.5 : 1)
                .attr("stroke-dasharray", (d:any) => d.type === 'tag' ? "3,3" : "");

            // SVG Defs (Glow Filter)
            const defs = svg.append("defs");
            const filter = defs.append("filter").attr("id", "glow");
            filter.append("feGaussianBlur").attr("stdDeviation", "2.5").attr("result", "coloredBlur");
            const feMerge = filter.append("feMerge");
            feMerge.append("feMergeNode").attr("in", "coloredBlur");
            feMerge.append("feMergeNode").attr("in", "SourceGraphic");

            const node = g.append("g")
                .selectAll("g")
                .data(nodes)
                .join("g")
                .call(d3.drag<any, any>()
                    .on("start", (e, d) => { if (!e.active) simulation?.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
                    .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
                    .on("end", (e, d) => { if (!e.active) simulation?.alphaTarget(0); d.fx = null; d.fy = null; })
                )
                .on("click", (e, d) => { 
                    e.stopPropagation(); 
                    onNodeClick(d.raw || { id: d.id, label: d.label, group: d.group }); 
                });

            node.append("circle")
                .attr("r", (d:any) => d.val)
                .attr("fill", (d:any) => d.color)
                .attr("stroke", "#1e293b")
                .attr("stroke-width", 2)
                .style("filter", "url(#glow)")
                .style("cursor", "pointer");

            node.append("text")
                .text((d:any) => d.label)
                .attr("text-anchor", "middle")
                .attr("dy", (d:any) => d.val + 12)
                .attr("fill", "#94a3b8")
                .attr("font-size", "10px")
                .style("pointer-events", "none")
                .style("user-select", "none");

            simulation.on("tick", () => {
                link
                    .attr("x1", (d:any) => d.source.x)
                    .attr("y1", (d:any) => d.source.y)
                    .attr("x2", (d:any) => d.target.x)
                    .attr("y2", (d:any) => d.target.y);
                node
                    .attr("transform", (d:any) => `translate(${d.x},${d.y})`);
            });

            const zoom = d3.zoom().scaleExtent([0.1, 5]).on("zoom", (e) => {
                g.attr("transform", e.transform);
            });
            svg.call(zoom as any);

        } catch (error) {
            console.error("D3 Graph Error:", error);
        }

        return () => {
            if (simulation) simulation.stop();
            // 使用變數中的 ref 進行 cleanup
            if (currentSvgRef) {
                d3.select(currentSvgRef).on(".zoom", null);
                currentSvgRef.innerHTML = "";
            }
        };

    // [Fix 3] 加入 onNodeClick 到依賴陣列
    }, [logs, mode, dimensions, onNodeClick]);

    return (
        <div ref={containerRef} className="w-full h-[500px] bg-[#0b1120] rounded-3xl overflow-hidden relative border border-slate-800 shadow-2xl">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-2 pointer-events-none">
                <div className="bg-slate-900/80 px-3 py-1 rounded-full text-xs text-emerald-400 font-mono flex items-center gap-2 border border-emerald-500/30 backdrop-blur">
                    <Activity size={12}/> Neon D3 Engine: ACTIVE
                </div>
                <div className="text-[10px] text-slate-500 font-mono ml-2">
                    Nodes: {stats.nodes} | Links: {stats.links}
                </div>
            </div>
            
            <div className="absolute top-4 right-4 z-20 flex gap-2">
                <button onClick={() => setMode('gravity')} className={`p-2 rounded-lg border transition-all ${mode==='gravity'?'bg-indigo-600 border-indigo-400 text-white':'bg-slate-800 border-slate-700 text-slate-400'}`}><Layers size={16}/></button>
                <button onClick={() => setMode('cluster')} className={`p-2 rounded-lg border transition-all ${mode==='cluster'?'bg-indigo-600 border-indigo-400 text-white':'bg-slate-800 border-slate-700 text-slate-400'}`}><LayoutGrid size={16}/></button>
            </div>

            <svg ref={svgRef} className="w-full h-full cursor-move block"></svg>
        </div>
    );
};

// [Fix 4] 設定 Display Name 並 Memo 化
export const NeuralGraph = memo(NeuralGraphComponent);
NeuralGraph.displayName = 'NeuralGraph';