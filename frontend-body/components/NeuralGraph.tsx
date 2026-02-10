'use client';

import React, { memo, useRef, useState, useMemo, useEffect } from 'react';
import * as d3 from 'd3';
import { Activity, Share2, Maximize2 } from 'lucide-react';
import { CoreEngine, NEON_PALETTE, LogEntry, GraphNode, GraphLink, GraphData } from '@/lib/ai/core';

interface NeuralGraphProps {
    logs: LogEntry[];
    onNodeClick?: (node: any) => void;
}

// [GRAPH v3.2] Force Directed Graph with Enhanced Neon Palette & Physics
export const NeuralGraph = memo(({ logs, onNodeClick }: NeuralGraphProps) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [stats, setStats] = useState({ nodes: 0, links: 0 });

    // Data Processing: Support both local logs and backend brain data
    const [remoteData, setRemoteData] = useState<GraphData | null>(null);

    useEffect(() => {
        const fetchGraph = async () => {
            try {
                const { cortex } = await import('@/lib/api/client');
                const data = await cortex.getBrainGraph(); // We need to add this to client.ts if missing
                setRemoteData(data);
            } catch (e) {
                console.warn("Failed to fetch remote brain graph, falling back to local logs", e);
            }
        };
        fetchGraph();
    }, [logs]); // Refresh when logs change to stay responsive

    const graphData = useMemo(() => {
        // If we have remote data (the truth from Supabase), use it!
        if (remoteData && remoteData.nodes.length > 0) return remoteData;

        // Fallback to local parsing for immediate feedback
        if (!logs || logs.length === 0) return { nodes: [], links: [] };
        return CoreEngine.parseGraphSeeds(logs);
    }, [logs, remoteData]);

    useEffect(() => {
        if (!graphData.nodes.length || !svgRef.current || !containerRef.current) return;

        const { clientWidth: width, clientHeight: height } = containerRef.current;
        if (width === 0 || height === 0) return;

        setStats({ nodes: graphData.nodes.length, links: graphData.links.length });

        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove(); // Clear previous render

        const g = svg.append("g");

        // Zoom functionality
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 5])
            .on("zoom", (event) => g.attr("transform", event.transform));
        svg.call(zoom);

        // Layers
        const linkLayer = g.append("g").attr("class", "links");
        const nodeLayer = g.append("g").attr("class", "nodes");
        const textLayer = g.append("g").attr("class", "labels");

        // Simulation Setup
        const simulation = d3.forceSimulation<GraphNode>(graphData.nodes)
            .force("link", d3.forceLink<GraphNode, GraphLink>(graphData.links).id(d => d.id).distance(80))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2).strength(0.08))
            .force("collide", d3.forceCollide().radius((d: any) => (d.val || 5) + 8).iterations(2));

        // Glow Filter Definition
        const defs = svg.append("defs");
        const filter = defs.append("filter").attr("id", "neon-glow");
        filter.append("feGaussianBlur").attr("stdDeviation", "2.5").attr("result", "coloredBlur");
        const feMerge = filter.append("feMerge");
        feMerge.append("feMergeNode").attr("in", "coloredBlur");
        feMerge.append("feMergeNode").attr("in", "SourceGraphic");

        // Draw Links
        const link = linkLayer
            .selectAll("line")
            .data(graphData.links)
            .join("line")
            .attr("stroke", NEON_PALETTE.SLATE)
            .attr("stroke-opacity", 0.3)
            .attr("stroke-width", (d: any) => Math.sqrt(d.value || 1));

        // Draw Nodes
        const node = nodeLayer
            .selectAll("g")
            .data(graphData.nodes)
            .join("circle")
            .attr("r", (d: any) => (d.val || 5) * 1.5)
            .attr("fill", (d: any) => {
                // [Visual Update] Cyberpunk Color Mapping
                // Log -> Cyan (Standard), Lime (High Mood), Pink (Alert)
                // Tag -> Violet

                if (d.group === 1 || d.group === 'log') {
                    const mood = (d.raw as any)?.metrics?.mood || 5;
                    if (mood >= 8) return NEON_PALETTE.NEON_LIME;
                    if (mood <= 3) return NEON_PALETTE.NEON_PINK; // or Red
                    return NEON_PALETTE.NEON_CYAN;
                }

                if (d.group === 2 || d.group === 'tag') {
                    return NEON_PALETTE.NEON_VIOLET;
                }

                if (d.group === 'person') {
                    return NEON_PALETTE.secondary; // Cyan/Blue for People
                }

                if (d.group === 'concept') {
                    return NEON_PALETTE.warning; // Yellow for Concepts
                }

                return NEON_PALETTE.primary; // Fallback Green for Projects/Others
            })
            .attr("stroke", "#0a0a0a")
            .attr("stroke-width", 2)
            .style("cursor", "grab")
            .style("filter", "url(#neon-glow)") // Apply Glow
            .call(d3.drag<any, any>()
                .on("start", (event, d) => {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                    d3.select(event.sourceEvent.target).style("cursor", "grabbing");
                })
                .on("drag", (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on("end", (event, d) => {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                    d3.select(event.sourceEvent.target).style("cursor", "grab");
                }));

        // Tooltip interaction
        const tooltip = d3.select("body").append("div")
            .attr("class", "absolute z-50 px-3 py-2 text-xs font-mono bg-black/90 border border-white/20 text-white rounded-xl shadow-2xl pointer-events-none opacity-0 backdrop-blur-md");

        node.on("mouseover", function (event, d: any) {
            d3.select(this)
                .transition().duration(200)
                .attr("r", (d.val || 5) * 2)
                .attr("stroke", "#fff");

            tooltip.transition().duration(200).style("opacity", 1);
            tooltip.html(`
                <div class="font-bold text-[#00ff9d]">${d.id}</div>
                <div class="text-slate-400 text-[10px]">${d.group === 1 ? 'LOG ENTRY' : 'TAG NODE'}</div>
            `)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 28) + "px");
        })
            .on("mouseout", function (event, d: any) {
                d3.select(this)
                    .transition().duration(200)
                    .attr("r", (d.val || 5) * 1.5)
                    .attr("stroke", "#0a0a0a");
                tooltip.transition().duration(500).style("opacity", 0);
            })
            .on("click", (event, d) => {
                if (onNodeClick) onNodeClick(d);
            });

        // Labels (Only for larger nodes or tags to avoid clutter)
        const label = textLayer
            .selectAll("text")
            .data(graphData.nodes.filter((n: GraphNode) => (n.val || 0) > 3 || n.group === 'tag'))
            .join("text")
            .attr("dy", (d: any) => (d.val || 5) * 1.5 + 12)
            .attr("text-anchor", "middle")
            .text((d: any) => d.id.length > 12 ? d.id.slice(0, 10) + '..' : d.id)
            .attr("fill", (d: any) => d.group === 'tag' ? NEON_PALETTE.NEON_VIOLET : "#94a3b8")
            .attr("font-size", "10px")
            .attr("font-family", "monospace")
            .attr("font-weight", "bold")
            .style("pointer-events", "none")
            .style("text-shadow", "0 0 5px rgba(0,0,0,0.8)");

        // Simulation Tick
        simulation.on("tick", () => {
            link
                .attr("x1", (d: any) => d.source.x)
                .attr("y1", (d: any) => d.source.y)
                .attr("x2", (d: any) => d.target.x)
                .attr("y2", (d: any) => d.target.y);

            node
                .attr("cx", (d: any) => d.x)
                .attr("cy", (d: any) => d.y);

            label
                .attr("x", (d: any) => d.x)
                .attr("y", (d: any) => d.y);
        });

        return () => {
            simulation.stop();
            tooltip.remove();
        };

    }, [graphData, onNodeClick]);

    return (
        <div ref={containerRef} className="w-full h-[400px] sm:h-[500px] lg:h-[600px] bg-[#050505] rounded-3xl overflow-hidden relative border border-slate-800 shadow-2xl group touch-none">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-1 pointer-events-none select-none">
                <div className="bg-black/40 px-3 py-1 rounded-full text-xs text-[#00ffff] font-mono flex items-center gap-2 border border-[#00ffff]/20 backdrop-blur shadow-[0_0_15px_rgba(0,255,255,0.1)]">
                    <Activity size={12} className="animate-pulse" /> NEURAL MAP v3.2
                </div>
                <div className="text-[10px] text-slate-500 font-mono ml-2 flex gap-3">
                    <span>Nodes: {stats.nodes}</span>
                    <span>Links: {stats.links}</span>
                </div>
            </div>

            {/* Interactive Hints */}
            <div className="absolute bottom-4 right-4 z-10 opacity-0 group-hover:opacity-100 transition-opacity text-[10px] text-slate-600 font-mono text-right pointer-events-none">
                SCROLL TO ZOOM<br />DRAG TO MOVE
            </div>

            <svg ref={svgRef} className="w-full h-full cursor-move"></svg>
        </div>
    );
});