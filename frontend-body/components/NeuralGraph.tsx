'use client';

import React, { memo, useRef, useState, useMemo, useEffect } from 'react';
import * as d3 from 'd3';
import { Activity } from 'lucide-react';
import { CoreEngine, NEON_PALETTE } from '@/lib/ai/core';

interface NeuralGraphProps {
    logs: any[];
    onNodeClick: (node: any) => void;
}

// [GRAPH v10.2.2] HIGH DENSITY NEON ENGINE - VISUAL STABILITY FIX
export const NeuralGraph = memo(({ logs, onNodeClick }: NeuralGraphProps) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [stats, setStats] = useState({ nodes: 0, links: 0 });

    const graphData = useMemo(() => {
        if (!logs || logs.length === 0) return { nodes: [], links: [] };

        const nodesMap = new Map();
        const links: any[] = [];

        logs.forEach(log => {
            const id = log.date;
            const seeds = CoreEngine.parseGraphSeeds(log.note, log.graphSeeds?.content);
            const tags = seeds.tags;
            const explicitLinks = seeds.links;

            if (!nodesMap.has(id)) {
                const mood = log.metrics?.mood || 5;
                const isSignal = log.isSignal;
                let color = NEON_PALETTE.INDIGO;
                if (isSignal) color = NEON_PALETTE.BLUE;
                else if (mood > 7) color = NEON_PALETTE.EMERALD;
                else if (mood < 4) color = NEON_PALETTE.ROSE;

                nodesMap.set(id, {
                    id,
                    group: 'date',
                    val: isSignal ? 16 : (8 + (log.metrics.focus * 0.5)),
                    label: id.slice(5),
                    color: color,
                    raw: log,
                    isSignal: isSignal
                });
            }

            tags.forEach((tag: string) => {
                if (!nodesMap.has(tag)) {
                    nodesMap.set(tag, {
                        id: tag,
                        group: 'tag',
                        val: 10,
                        label: tag,
                        color: NEON_PALETTE.PINK
                    });
                }
                links.push({ source: id, target: tag, type: 'tag' });
            });

            explicitLinks.forEach((targetDate: string) => {
                if (!nodesMap.has(targetDate)) {
                    nodesMap.set(targetDate, {
                        id: targetDate,
                        group: 'stub',
                        val: 5,
                        label: targetDate.slice(5),
                        color: NEON_PALETTE.SLATE
                    });
                }
                links.push({ source: id, target: targetDate, type: 'manual' });
            });
        });

        return { nodes: Array.from(nodesMap.values()), links };
    }, [logs]);

    useEffect(() => {
        if (!graphData.nodes.length || !svgRef.current || !containerRef.current) return;

        const { clientWidth: width, clientHeight: height } = containerRef.current;
        if (width === 0 || height === 0) return;

        setStats({ nodes: graphData.nodes.length, links: graphData.links.length });

        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove();

        const g = svg.append("g");
        const linkLayer = g.append("g").attr("class", "links");
        const nodeLayer = g.append("g").attr("class", "nodes");
        const textLayer = g.append("g").attr("class", "labels");

        const zoom = d3.zoom()
            .scaleExtent([0.1, 5])
            .on("zoom", (e: any) => g.attr("transform", e.transform));
        svg.call(zoom as any);

        const simulation = d3.forceSimulation(graphData.nodes as any)
            .force("link", d3.forceLink(graphData.links).id((d: any) => d.id).distance(60))
            .force("charge", d3.forceManyBody().strength(-120))
            .force("center", d3.forceCenter(width / 2, height / 2).strength(0.08))
            .force("collide", d3.forceCollide().radius((d: any) => d.val + 2).iterations(3));

        const defs = svg.append("defs");
        const filter = defs.append("filter").attr("id", "glow");
        filter.append("feGaussianBlur").attr("stdDeviation", "2.5").attr("result", "coloredBlur");
        const feMerge = filter.append("feMerge");
        feMerge.append("feMergeNode").attr("in", "coloredBlur");
        feMerge.append("feMergeNode").attr("in", "SourceGraphic");

        const link = linkLayer
            .selectAll("line")
            .data(graphData.links)
            .join("line")
            .attr("stroke", "#cbd5e1")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", (d: any) => d.type === 'manual' ? 1.5 : 0.8)
            .attr("stroke-dasharray", (d: any) => d.type === 'tag' ? "2,2" : "0");

        // Drag functions need to be defined inside or accessible
        const dragstarted = (e: any, d: any) => {
            if (!e.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        };
        const dragged = (e: any, d: any) => {
            d.fx = e.x;
            d.fy = e.y;
        };
        const dragended = (e: any, d: any) => {
            if (!e.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        };

        const node = nodeLayer
            .selectAll("g")
            .data(graphData.nodes)
            .join("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended) as any);

        node.append("circle")
            .filter((d: any) => d.isSignal)
            .attr("r", (d: any) => d.val + 6)
            .attr("fill", (d: any) => d.color)
            .attr("opacity", 0.4)
            .style("filter", "url(#glow)");

        node.append("circle")
            .attr("r", (d: any) => d.val)
            .attr("fill", (d: any) => d.color)
            .attr("stroke", "#0f172a")
            .attr("stroke-width", 2)
            .style("cursor", "pointer")
            .on("click", (e, d: any) => {
                e.stopPropagation();
                // Construct a safe node object to pass back
                const nodeData = d.raw ? { ...d.raw, group: d.group } : { id: d.id, label: d.label, group: d.group, tags: [], note: "Stub Node", graphSeeds: { tags: '', links: '', content: '' } };
                onNodeClick(nodeData);
            })
            .on("mouseover", function () { d3.select(this).transition().duration(200).attr("stroke", "#fff").attr("stroke-width", 3); })
            .on("mouseout", function () { d3.select(this).transition().duration(200).attr("stroke", "#0f172a").attr("stroke-width", 2); });

        const label = textLayer
            .selectAll("text")
            .data(graphData.nodes)
            .join("text")
            .attr("dy", (d: any) => d.val + 12)
            .attr("text-anchor", "middle")
            .text((d: any) => d.label.length > 8 ? d.label.slice(0, 6) + '..' : d.label)
            .attr("fill", "#94a3b8")
            .attr("font-size", "9px")
            .attr("font-family", "monospace")
            .style("pointer-events", "none")
            .style("text-shadow", "0 2px 4px rgba(0,0,0,1)");

        simulation.on("tick", () => {
            link
                .attr("x1", (d: any) => d.source.x)
                .attr("y1", (d: any) => d.source.y)
                .attr("x2", (d: any) => d.target.x)
                .attr("y2", (d: any) => d.target.y);

            node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
            label.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
        });

        return () => simulation.stop();

    }, [graphData, onNodeClick]);

    return (
        <div ref={containerRef} className="w-full h-[500px] bg-slate-900 rounded-3xl overflow-hidden relative border border-slate-800 shadow-2xl">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-1 pointer-events-none select-none">
                <div className="bg-slate-900/80 px-3 py-1 rounded-full text-xs text-emerald-400 font-mono flex items-center gap-2 border border-emerald-500/30 backdrop-blur">
                    <Activity size={12} /> Neon D3 Engine: STABLE
                </div>
                <div className="text-[10px] text-slate-500 font-mono ml-2">
                    Nodes: {stats.nodes} | Links: {stats.links}
                </div>
            </div>
            <svg ref={svgRef} className="w-full h-full cursor-move"></svg>
        </div>
    );
});