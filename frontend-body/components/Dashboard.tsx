'use client';

import React, { useState, useCallback } from 'react';
import {
    ComposedChart, Area, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Activity, Rocket, Edit3, Eye, Filter, Target, FileText } from 'lucide-react';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';

// Helper for safe loading CCA data locally or from props? 
// For now, let's assume parent passes data or we use local state if standalone.
// BUT, Dashboard in V3 might fetch from backend.
// Let's stick to the Legacy UI which is "Static Prop" based mostly, allowing for interactivity.

interface DashboardProps {
    logs?: any[]; // Optional if we fetch or use context
    ccaData?: any;
    onUpdateCCA?: (month: string, field: string, value: string) => void;
    onUpgradeSystem?: (month: string) => void;
}

export const Dashboard = ({ logs = [], ccaData = {}, onUpdateCCA, onUpgradeSystem }: DashboardProps) => {
    // Local state for Month selection
    const [dashboardMonth, setDashboardMonth] = useState(new Date().toISOString().slice(0, 7));
    const [isEditingReview, setIsEditingReview] = useState(false);

    // Filter Logs
    const filteredLogs = logs.filter(l => l.date.startsWith(dashboardMonth));
    const data = filteredLogs.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    const handleUpdate = (val: string) => {
        if (onUpdateCCA) onUpdateCCA(dashboardMonth, 'review', val);
    };

    return (
        <div className="space-y-6 pb-24 animate-fade-in">
            {/* Month Selector */}
            <div className="flex justify-between items-center bg-white p-3 rounded-2xl shadow-sm border border-slate-100">
                <div className="flex items-center gap-2 text-slate-700">
                    <Filter className="w-4 h-4 text-indigo-500" />
                    <span className="text-sm font-bold">Month View</span>
                </div>
                <input
                    type="month"
                    value={dashboardMonth}
                    onChange={(e) => setDashboardMonth(e.target.value)}
                    className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-sm font-mono outline-none focus:ring-2 focus:ring-indigo-100"
                />
            </div>

            {/* Trends Chart */}
            <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-200 h-64">
                <h3 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-indigo-500" /> 近期趨勢 (Recent Trends)
                </h3>
                <div style={{ width: '100%', height: '100%', minHeight: '200px' }}>
                    <ResponsiveContainer>
                        <ComposedChart data={data} style={{ cursor: 'pointer' }}>
                            <defs>
                                <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v: string) => v.slice(8)} axisLine={false} tickLine={false} />
                            <YAxis yAxisId="left" orientation="left" stroke="#6366f1" hide domain={[0, 10]} />
                            <YAxis yAxisId="right" orientation="right" stroke="#3b82f6" hide />
                            <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                            <Area yAxisId="left" type="monotone" dataKey="metrics.mood" stroke="#6366f1" fill="url(#colorMood)" strokeWidth={3} />
                            <Line yAxisId="left" type="monotone" dataKey="metrics.focus" stroke="#f43f5e" strokeWidth={2} dot={false} />
                            <Bar yAxisId="right" dataKey="metrics.deepWork" fill="#93c5fd" opacity={0.3} barSize={20} radius={[4, 4, 0, 0]} />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* CCA Review */}
            <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-100">
                <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-emerald-500" />
                        <h3 className="text-sm font-bold text-slate-700">月度復盤 (CCA)</h3>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => setIsEditingReview(!isEditingReview)} className="p-1.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-500">
                            {isEditingReview ? <Eye className="w-3 h-3" /> : <Edit3 className="w-3 h-3" />}
                        </button>
                        <button
                            onClick={() => onUpgradeSystem && onUpgradeSystem(dashboardMonth)}
                            className="text-[10px] bg-emerald-50 text-emerald-600 px-3 py-1 rounded-lg hover:bg-emerald-100 font-bold flex items-center gap-1 border border-emerald-200"
                        >
                            <Rocket className="w-3 h-3" /> 升級系統
                        </button>
                    </div>
                </div>

                {isEditingReview ? (
                    <textarea
                        value={ccaData[dashboardMonth]?.review || ''}
                        onChange={(e) => handleUpdate(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm resize-none outline-none h-48 font-mono"
                        placeholder="Paste your CCA Agent report here..."
                    />
                ) : (
                    <div className="h-48 overflow-y-auto text-sm text-slate-600 font-mono bg-slate-50 p-3 rounded-xl custom-scrollbar border border-slate-100">
                        {ccaData[dashboardMonth]?.review ? (
                            <MarkdownRenderer content={ccaData[dashboardMonth].review} />
                        ) : (
                            <span className="text-slate-400 italic flex flex-col items-center justify-center h-full gap-2">
                                <FileText className="w-6 h-6 opacity-20" />
                                請貼上報告或使用 Agent 分析...
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};