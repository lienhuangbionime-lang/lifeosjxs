'use client';

import React, { useState, useMemo } from 'react';
import {
    ComposedChart, Area, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Activity, Rocket, Edit3, Eye, Filter, Target, FileText, Hash, Zap } from 'lucide-react';
import { CortexChat } from './CortexChat';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';
import { NEON_PALETTE, CoreEngine } from '@/lib/ai/core';
import { motion } from 'framer-motion';

interface DashboardProps {
    logs?: any[];
    ccaData?: any;
    onUpdateCCA?: (month: string, field: string, value: string) => void;
    onUpgradeSystem?: (month: string) => void;
}

export const Dashboard = ({ logs = [], ccaData = {}, onUpdateCCA, onUpgradeSystem }: DashboardProps) => {
    // Local state for Month selection
    const [dashboardMonth, setDashboardMonth] = useState(new Date().toISOString().slice(0, 7));
    const [isEditingReview, setIsEditingReview] = useState(false);

    // Filter Logs & Process Data
    const { chartData, tagCloud } = useMemo(() => {
        const filtered = logs.filter(l => l.date.startsWith(dashboardMonth));
        const sorted = filtered.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        // Tag Cloud Logic
        const tagsMap = new Map<string, number>();
        sorted.forEach(l => {
            const tags = l.tags || (l.note.match(/#([\w\u4e00-\u9fa5]+)/g) || []).map((t: string) => t.slice(1));
            tags.forEach((t: string) => tagsMap.set(t, (tagsMap.get(t) || 0) + 1));
        });
        const tags = Array.from(tagsMap.entries())
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 10); // Top 10

        return { chartData: sorted, tagCloud: tags };
    }, [logs, dashboardMonth]);

    const handleUpdate = (val: string) => {
        if (onUpdateCCA) onUpdateCCA(dashboardMonth, 'review', val);
    };

    return (
        <div className="space-y-6 pb-24 animate-fade-in text-slate-200">
            {/* Month Selector */}
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-2xl shadow-sm border border-slate-800 backdrop-blur-sm">
                <div className="flex items-center gap-2 text-indigo-400">
                    <Filter className="w-4 h-4" />
                    <span className="text-sm font-bold uppercase tracking-wider">Timeframe</span>
                </div>
                <input
                    type="month"
                    value={dashboardMonth}
                    onChange={(e) => setDashboardMonth(e.target.value)}
                    className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm font-mono outline-none focus:ring-2 focus:ring-indigo-500/50 text-white"
                />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Mood Trend */}
                <div className="bg-slate-900/50 p-5 rounded-3xl shadow-xl border border-slate-800 h-72 backdrop-blur-sm">
                    <h3 className="text-xs font-bold text-slate-400 mb-4 flex items-center gap-2 uppercase tracking-wider">
                        <Activity className="w-4 h-4 text-emerald-400" /> Flow State (Mood)
                    </h3>
                    <div style={{ width: '100%', height: '85%' }}>
                        <ResponsiveContainer>
                            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={NEON_PALETTE.NEON_LIME} stopOpacity={0.2} />
                                        <stop offset="95%" stopColor={NEON_PALETTE.NEON_LIME} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={(v: string) => v.slice(8)} axisLine={false} tickLine={false} />
                                <YAxis yAxisId="left" stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} domain={[0, 10]} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '12px', border: '1px solid #334155', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)', background: '#0f172a', color: '#fff' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area yAxisId="left" type="monotone" dataKey="metrics.mood" stroke={NEON_PALETTE.NEON_LIME} fill="url(#colorMood)" strokeWidth={3} activeDot={{ r: 6, fill: "#fff" }} />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Productivity Chart */}
                <div className="bg-slate-900/50 p-5 rounded-3xl shadow-xl border border-slate-800 h-72 backdrop-blur-sm">
                    <h3 className="text-xs font-bold text-slate-400 mb-4 flex items-center gap-2 uppercase tracking-wider">
                        <Rocket className="w-4 h-4 text-pink-500" /> Deep Work Output
                    </h3>
                    <div style={{ width: '100%', height: '85%' }}>
                        <ResponsiveContainer>
                            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={(v: string) => v.slice(8)} axisLine={false} tickLine={false} />
                                <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} />
                                <Tooltip cursor={{ fill: '#1e293b' }} contentStyle={{ borderRadius: '12px', border: '1px solid #334155', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)', background: '#0f172a', color: '#fff' }} />
                                <Bar dataKey="metrics.deepWork" fill={NEON_PALETTE.NEON_PINK} radius={[4, 4, 0, 0]} barSize={12}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.metrics.deepWork > 180 ? NEON_PALETTE.NEON_CYAN : NEON_PALETTE.NEON_PINK} />
                                    ))}
                                </Bar>
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Row 3: Tag Cloud & CCA */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Tag Cloud (Takes 1 Col) */}
                <div className="bg-slate-900/50 p-6 rounded-3xl shadow-xl border border-slate-800 relative overflow-hidden backdrop-blur-sm">
                    <h3 className="text-xs font-bold text-slate-400 mb-4 flex items-center gap-2 uppercase tracking-wider">
                        <Hash className="w-4 h-4 text-violet-400" /> Neural Tags
                    </h3>
                    <div className="flex flex-wrap gap-2">
                        {tagCloud.length > 0 ? tagCloud.map((tag, i) => (
                            <div key={tag.name} className="flex items-center gap-1.5 bg-slate-800/80 px-2 py-1 rounded-md border border-slate-700/50">
                                <span className="text-xs font-mono text-violet-300">#{tag.name}</span>
                                <span className="text-[10px] font-bold text-slate-500 bg-slate-900 px-1 rounded">{tag.count}</span>
                            </div>
                        )) : (
                            <div className="text-slate-600 text-xs italic">No tags found for this month.</div>
                        )}
                    </div>
                    {/* Decorative bg element */}
                    <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-violet-500/10 rounded-full blur-2xl pointer-events-none"></div>
                </div>

                {/* CCA Review UI (Takes 2 Cols) */}
                <div className="lg:col-span-2 bg-slate-900 text-white p-6 rounded-3xl shadow-xl relative overflow-hidden border border-slate-800">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>

                    <div className="flex justify-between items-start mb-4 relative z-10">
                        <div>
                            <div className="flex items-center gap-2 text-emerald-400 mb-1">
                                <Target className="w-4 h-4" />
                                <span className="text-xs font-bold tracking-wider uppercase">Cortex Analysis</span>
                            </div>
                            <h3 className="text-xl font-bold">Monthly Review (CCA)</h3>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => setIsEditingReview(!isEditingReview)} className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
                                {isEditingReview ? <Eye className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
                            </button>
                        </div>
                    </div>

                    <div className="relative z-10 bg-slate-800/50 rounded-2xl p-4 border border-slate-700/50">
                        {isEditingReview ? (
                            <textarea
                                value={ccaData[dashboardMonth]?.review || ''}
                                onChange={(e) => handleUpdate(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-sm resize-none outline-none h-40 font-mono text-slate-300 focus:border-indigo-500 transition-colors"
                                placeholder="Paste your CCA Agent report here..."
                            />
                        ) : (
                            <div className="h-40 overflow-y-auto text-sm text-slate-300 font-mono custom-scrollbar leading-relaxed">
                                {ccaData[dashboardMonth]?.review ? (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ duration: 0.5 }}
                                    >
                                        <MarkdownRenderer content={ccaData[dashboardMonth].review} />
                                    </motion.div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-500 opacity-60">
                                        <FileText className="w-8 h-8" />
                                        <span className="text-xs">No analysis data for this month.</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* --- Cortex Chat Overlay --- */}
            <CortexChat />
        </div>
    );
};
