'use client';

import React, { useState } from 'react';
import { List as ListIcon, Filter, Zap, TrendingUp, Clock, Activity, Calendar } from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS, NEON_PALETTE } from '@/frontend-body/lib/ai/core';

// 輔助：取得 Mood 對應顏色
const getMoodColor = (mood: number) => {
    if (mood >= 8) return 'bg-emerald-500';
    if (mood <= 3) return 'bg-rose-500';
    return 'bg-indigo-500';
};

export const HistoryView = ({ logs }: { logs: any[] }) => {
    const [searchTerm, setSearchTerm] = useState('');
    
    // 過濾與排序
    const filteredLogs = logs.filter(log => (log.content + log.date).toLowerCase().includes(searchTerm.toLowerCase()));
    const sortedLogs = [...filteredLogs].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    return (
        <div className="h-full flex flex-col pb-20">
            {/* Header */}
            <div className="flex justify-between items-center mb-6 px-2">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <ListIcon className="text-indigo-400" /> Time Capsule
                </h2>
                <input 
                    type="text" 
                    placeholder="Search..." 
                    value={searchTerm} 
                    onChange={(e) => setSearchTerm(e.target.value)} 
                    className="bg-slate-800 rounded-full text-xs text-white border border-slate-700 px-4 py-2 w-32 focus:w-48 transition-all outline-none"
                />
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto space-y-4 px-2 custom-scrollbar">
                {sortedLogs.map((log) => {
                    const insight = CoreEngine.extractInsight(log.content || log.note); // 支援新舊欄位
                    const moodColor = getMoodColor(log.mood || log.metrics?.mood || 5);
                    const activeHabits = log.habits ? Object.keys(log.habits).filter(k => log.habits[k]) : [];

                    return (
                        <div key={log.id || log.date} className="bg-[#1e293b] rounded-2xl border border-slate-700 overflow-hidden relative group hover:border-indigo-500/50 transition-all">
                            {/* Mood Bar */}
                            <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${moodColor}`} />

                            <div className="p-5 pl-6">
                                {/* Top Row: Date & Metrics */}
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <h3 className="text-lg font-black text-white font-mono tracking-tight">{log.date}</h3>
                                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                                            {new Date(log.date).toLocaleDateString('en-US', {weekday:'short'})}
                                        </span>
                                    </div>
                                    <div className="flex gap-2">
                                        <Badge icon={Activity} val={log.mood || log.metrics?.mood} color="indigo" />
                                        <Badge icon={Zap} val={log.focus || log.metrics?.focus} color="amber" />
                                    </div>
                                </div>

                                {/* Content Preview */}
                                <p className="text-sm text-slate-300 leading-relaxed mb-4 line-clamp-3 font-sans">
                                    {insight.text}
                                </p>

                                {/* Habits & Footer */}
                                <div className="flex justify-between items-center pt-3 border-t border-slate-700/50">
                                    <div className="flex gap-2">
                                        {activeHabits.map(hId => {
                                            const habitConfig = DEFAULT_HABITS.find(h => h.id === hId);
                                            if(!habitConfig) return null;
                                            const Icon = CoreEngine.getIconComponent(habitConfig.icon);
                                            return (
                                                <div key={hId} className="p-1.5 bg-slate-800 rounded-lg text-slate-400" title={habitConfig.label}>
                                                    <Icon size={12} />
                                                </div>
                                            )
                                        })}
                                    </div>
                                    {/* Tag Visuals */}
                                    <div className="flex gap-1">
                                        {/* 這裡未來可顯示 graphSeeds tags */}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// 小元件：指標 Badge
const Badge = ({ icon: Icon, val, color }: any) => (
    <div className={`flex items-center gap-1 px-2 py-1 rounded-lg bg-${color}-500/10 text-${color}-400 border border-${color}-500/20`}>
        <Icon size={10} />
        <span className="text-[10px] font-bold">{val ?? '-'}</span>
    </div>
);