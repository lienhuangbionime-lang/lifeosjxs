// 檔案位置: src/components/NeuralGraph.tsx
"use client";
import React, { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { Activity, Layers, LayoutGrid, GitGraph, Brain } from 'lucide-react';
import { NEON_PALETTE, CoreEngine } from '@/lib/ai/core';

export const NeuralGraph = ({ logs, onNodeClick }: { logs: any[], onNodeClick: (n:any)=>void }) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [mode, setMode] = useState('gravity');
    const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });

    const { nodes, links } = useMemo(() => {
        if (!logs || logs.length === 0) return { nodes: [], links: [] };
        
        // --- 這裡是你原本的高密度節點生成邏輯 ---
        const _nodes: any[] = []; 
        const _links: any[] = []; 
        const nodesMap = new Map();

        logs.forEach(log => {
            const id = log.date;
            const seeds = CoreEngine.parseGraphSeeds(log.note, log.graphSeeds?.content);
            
            if (!nodesMap.has(id)) {
                // 視覺邏輯：根據 Mood 決定顏色
                const mood = log.metrics?.mood || 5;
                let color = NEON_PALETTE.INDIGO;
                if (mood > 7) color = NEON_PALETTE.EMERALD;
                else if (mood < 4) color = NEON_PALETTE.ROSE;

                const node = { 
                    id, 
                    val: 10 + (log.metrics.focus * 1.5), // 大小隨專注度變化
                    label: id.slice(5), 
                    color, 
                    raw: log 
                };
                _nodes.push(node);
                nodesMap.set(id, node);
            }
            
            // 建立 Tag 與連結
            seeds.tags.forEach((tag: string) => {
                if(!nodesMap.has(tag)) {
                    const tagNode = { id: tag, val: 8, label: tag, color: NEON_PALETTE.PINK, group: 'tag' };
                    _nodes.push(tagNode);
                    nodesMap.set(tag, tagNode);
                }
                _links.push({ source: id, target: tag, type: 'tag' });
            });
        });

        return { nodes: _nodes, links: _links };
    }, [logs]);

    // --- D3 渲染引擎 (Neon Engine) ---
    useEffect(() => {
        if (!nodes.length || !svgRef.current || !containerRef.current) return;
        const { clientWidth: width, clientHeight: height } = containerRef.current;

        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove();

        const g = svg.append("g");
        
        // 物理模擬參數 (High Density Cluster)
        const simulation = d3.forceSimulation(nodes as any)
            .force("link", d3.forceLink(links).id((d:any) => d.id).distance(60))
            .force("charge", d3.forceManyBody().strength(-120)) // 較小的斥力讓氣泡群聚
            .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))
            .force("collide", d3.forceCollide().radius((d:any) => d.val + 2).iterations(2));

        // 繪製連結
        const link = g.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("stroke", "#6366f1")
            .attr("stroke-opacity", 0.2)
            .attr("stroke-width", 1);

        // 繪製節點 (含光暈濾鏡)
        const defs = svg.append("defs");
        const filter = defs.append("filter").attr("id", "glow");
        filter.append("feGaussianBlur").attr("stdDeviation", "2.5").attr("result", "coloredBlur");
        const feMerge = filter.append("feMerge");
        feMerge.append("feMergeNode").attr("in", "coloredBlur");
        feMerge.append("feMergeNode").attr("in", "SourceGraphic");

        const node = g.append("g")
            .selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("r", (d:any) => d.val)
            .attr("fill", (d:any) => d.color)
            .attr("stroke", "#1e293b")
            .attr("stroke-width", 2)
            .style("filter", "url(#glow)")
            .style("cursor", "pointer")
            .call(d3.drag<any, any>()
                .on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
                .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
                .on("end", (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
            )
            .on("click", (e, d) => { e.stopPropagation(); onNodeClick(d.raw || d); });

        // 繪製標籤
        const label = g.append("g")
            .selectAll("text")
            .data(nodes)
            .join("text")
            .text((d:any) => d.label)
            .attr("text-anchor", "middle")
            .attr("dy", (d:any) => d.val + 12)
            .attr("fill", "#94a3b8")
            .attr("font-size", "10px")
            .style("pointer-events", "none");

        simulation.on("tick", () => {
            link
                .attr("x1", (d:any) => d.source.x)
                .attr("y1", (d:any) => d.source.y)
                .attr("x2", (d:any) => d.target.x)
                .attr("y2", (d:any) => d.target.y);
            node
                .attr("cx", (d:any) => d.x)
                .attr("cy", (d:any) => d.y);
            label
                .attr("x", (d:any) => d.x)
                .attr("y", (d:any) => d.y);
        });

        // Zoom Logic
        const zoom = d3.zoom().scaleExtent([0.1, 5]).on("zoom", (e) => {
            g.attr("transform", e.transform);
            setTransform(e.transform);
        });
        svg.call(zoom as any);

        return () => simulation.stop();
    }, [nodes, links]);

    return (
        <div ref={containerRef} className="w-full h-[500px] bg-[#0b1120] rounded-3xl overflow-hidden relative border border-slate-800 shadow-2xl">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-2 pointer-events-none">
                <div className="bg-slate-900/80 px-3 py-1 rounded-full text-xs text-emerald-400 font-mono flex items-center gap-2 border border-emerald-500/30 backdrop-blur">
                    <Activity size={12}/> Neon D3 Engine: ACTIVE
                </div>
            </div>
            <svg ref={svgRef} className="w-full h-full cursor-move"></svg>
        </div>
    );
};
