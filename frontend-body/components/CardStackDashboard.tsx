'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import {
    Activity, Rocket, Hash, TrendingUp,
    Calendar, ChevronLeft, ChevronRight, Sparkles
} from 'lucide-react';
import {
    ComposedChart, Area, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { NEON_PALETTE } from '@/lib/ai/core';
import { CortexChat } from './CortexChat';

interface CardStackDashboardProps {
    logs?: any[];
}

// 定義卡片類型
type CardType = 'overview' | 'mood' | 'productivity' | 'tags';

interface DashboardCard {
    id: CardType;
    title: string;
    icon: any;
    color: string;
    gradient: string;
}

const CARDS: DashboardCard[] = [
    {
        id: 'overview',
        title: 'Overview',
        icon: Sparkles,
        color: 'indigo',
        gradient: 'from-indigo-500/20 to-purple-500/20'
    },
    {
        id: 'mood',
        title: 'Flow State',
        icon: Activity,
        color: 'emerald',
        gradient: 'from-emerald-500/20 to-teal-500/20'
    },
    {
        id: 'productivity',
        title: 'Deep Work',
        icon: Rocket,
        color: 'pink',
        gradient: 'from-pink-500/20 to-rose-500/20'
    },
    {
        id: 'tags',
        title: 'Neural Tags',
        icon: Hash,
        color: 'violet',
        gradient: 'from-violet-500/20 to-fuchsia-500/20'
    },
];

export const CardStackDashboard = ({ logs = [] }: CardStackDashboardProps) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [dashboardMonth, setDashboardMonth] = useState(new Date().toISOString().slice(0, 7));

    // 處理數據
    const processedData = React.useMemo(() => {
        const filtered = logs.filter(l => l.date?.startsWith(dashboardMonth));
        const sorted = filtered.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        // Tag Cloud
        const tagsMap = new Map<string, number>();
        sorted.forEach(l => {
            const tags = l.tags || (l.note?.match(/#([\w\u4e00-\u9fa5]+)/g) || []).map((t: string) => t.slice(1));
            tags.forEach((t: string) => tagsMap.set(t, (tagsMap.get(t) || 0) + 1));
        });
        const tagCloud = Array.from(tagsMap.entries())
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 12);

        // 統計數據
        const totalEntries = sorted.length;
        const avgMood = sorted.length > 0
            ? sorted.reduce((sum, l) => sum + (l.metrics?.mood || 5), 0) / sorted.length
            : 5;
        const totalDeepWork = sorted.reduce((sum, l) => sum + (l.metrics?.deepWork || 0), 0);

        return { chartData: sorted, tagCloud, totalEntries, avgMood, totalDeepWork };
    }, [logs, dashboardMonth]);

    // 滑動處理
    const handleDragEnd = (event: any, info: PanInfo) => {
        const threshold = 50;
        if (info.offset.x > threshold && currentIndex > 0) {
            setCurrentIndex(currentIndex - 1);
        } else if (info.offset.x < -threshold && currentIndex < CARDS.length - 1) {
            setCurrentIndex(currentIndex + 1);
        }
    };

    const goToNext = () => {
        if (currentIndex < CARDS.length - 1) {
            setCurrentIndex(currentIndex + 1);
        }
    };

    const goToPrev = () => {
        if (currentIndex > 0) {
            setCurrentIndex(currentIndex - 1);
        }
    };

    // 渲染卡片內容
    const renderCardContent = (cardId: CardType) => {
        switch (cardId) {
            case 'overview':
                return (
                    <div className="space-y-6">
                        <div className="grid grid-cols-3 gap-4">
                            <StatCard
                                label="Total Entries"
                                value={processedData.totalEntries.toString()}
                                icon={Calendar}
                                color="indigo"
                            />
                            <StatCard
                                label="Avg Mood"
                                value={processedData.avgMood.toFixed(1)}
                                icon={Activity}
                                color="emerald"
                            />
                            <StatCard
                                label="Deep Work"
                                value={`${Math.floor(processedData.totalDeepWork / 60)}h`}
                                icon={Rocket}
                                color="pink"
                            />
                        </div>

                        <div className="bg-slate-800/30 rounded-2xl p-4 border border-slate-700/50">
                            <h4 className="text-sm font-bold text-slate-300 mb-3 flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-indigo-400" />
                                Monthly Trend
                            </h4>
                            <div className="h-48">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ComposedChart data={processedData.chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                        <defs>
                                            <linearGradient id="overviewGradient" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor={NEON_PALETTE.NEON_CYAN} stopOpacity={0.3} />
                                                <stop offset="95%" stopColor={NEON_PALETTE.NEON_CYAN} stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                                        <XAxis
                                            dataKey="date"
                                            tick={{ fontSize: 10, fill: '#64748b' }}
                                            tickFormatter={(v: string) => v.slice(8)}
                                            axisLine={false}
                                            tickLine={false}
                                        />
                                        <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} domain={[0, 10]} />
                                        <Tooltip
                                            contentStyle={{
                                                borderRadius: '12px',
                                                border: '1px solid #334155',
                                                background: '#0f172a',
                                                color: '#fff'
                                            }}
                                        />
                                        <Area
                                            type="monotone"
                                            dataKey="metrics.mood"
                                            stroke={NEON_PALETTE.NEON_CYAN}
                                            fill="url(#overviewGradient)"
                                            strokeWidth={2}
                                        />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                );

            case 'mood':
                return (
                    <div className="h-full flex flex-col">
                        <h4 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2">
                            <Activity className="w-4 h-4 text-emerald-400" />
                            Flow State Analysis
                        </h4>
                        <div className="flex-1">
                            <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart data={processedData.chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                                    <defs>
                                        <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={NEON_PALETTE.NEON_LIME} stopOpacity={0.3} />
                                            <stop offset="95%" stopColor={NEON_PALETTE.NEON_LIME} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fontSize: 10, fill: '#64748b' }}
                                        tickFormatter={(v: string) => v.slice(8)}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} domain={[0, 10]} />
                                    <Tooltip
                                        contentStyle={{
                                            borderRadius: '12px',
                                            border: '1px solid #334155',
                                            background: '#0f172a',
                                            color: '#fff'
                                        }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="metrics.mood"
                                        stroke={NEON_PALETTE.NEON_LIME}
                                        fill="url(#colorMood)"
                                        strokeWidth={3}
                                        activeDot={{ r: 6, fill: "#fff" }}
                                    />
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                );

            case 'productivity':
                return (
                    <div className="h-full flex flex-col">
                        <h4 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2">
                            <Rocket className="w-4 h-4 text-pink-400" />
                            Deep Work Output
                        </h4>
                        <div className="flex-1">
                            <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart data={processedData.chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fontSize: 10, fill: '#64748b' }}
                                        tickFormatter={(v: string) => v.slice(8)}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} />
                                    <Tooltip
                                        contentStyle={{
                                            borderRadius: '12px',
                                            border: '1px solid #334155',
                                            background: '#0f172a',
                                            color: '#fff'
                                        }}
                                    />
                                    <Bar dataKey="metrics.deepWork" fill={NEON_PALETTE.NEON_PINK} radius={[4, 4, 0, 0]} barSize={12}>
                                        {processedData.chartData.map((entry, index) => (
                                            <Cell
                                                key={`cell-${index}`}
                                                fill={entry.metrics?.deepWork > 180 ? NEON_PALETTE.NEON_CYAN : NEON_PALETTE.NEON_PINK}
                                            />
                                        ))}
                                    </Bar>
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                );

            case 'tags':
                return (
                    <div className="h-full flex flex-col">
                        <h4 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2">
                            <Hash className="w-4 h-4 text-violet-400" />
                            Neural Tags Cloud
                        </h4>
                        <div className="flex-1 overflow-y-auto custom-scrollbar">
                            <div className="flex flex-wrap gap-2">
                                {processedData.tagCloud.length > 0 ? processedData.tagCloud.map((tag, i) => (
                                    <motion.div
                                        key={tag.name}
                                        initial={{ opacity: 0, scale: 0.8 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="flex items-center gap-1.5 bg-slate-800/80 px-3 py-2 rounded-xl border border-violet-500/30 hover:border-violet-400/50 transition-colors"
                                    >
                                        <span className="text-sm font-mono text-violet-300">#{tag.name}</span>
                                        <span className="text-xs font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded-full">
                                            {tag.count}
                                        </span>
                                    </motion.div>
                                )) : (
                                    <div className="text-slate-500 text-sm italic">No tags found for this month.</div>
                                )}
                            </div>
                        </div>
                    </div>
                )

            default:
                return null;
        }
    };

    return (
        <div className="relative h-full w-full pb-24 overflow-hidden">
            {/* Month Selector */}
            <div className="mb-6 flex justify-between items-center bg-slate-900/50 p-3 rounded-2xl border border-slate-800 backdrop-blur-sm">
                <div className="flex items-center gap-2 text-indigo-400">
                    <Calendar className="w-4 h-4" />
                    <span className="text-sm font-bold uppercase tracking-wider">Timeframe</span>
                </div>
                <input
                    type="month"
                    value={dashboardMonth}
                    onChange={(e) => setDashboardMonth(e.target.value)}
                    className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm font-mono outline-none focus:ring-2 focus:ring-indigo-500/50 text-white"
                />
            </div>

            {/* Card Stack Container */}
            <div className="relative h-[500px] sm:h-[600px]">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentIndex}
                        drag="x"
                        dragConstraints={{ left: 0, right: 0 }}
                        dragElastic={0.2}
                        onDragEnd={handleDragEnd}
                        initial={{ opacity: 0, x: 100, scale: 0.95 }}
                        animate={{ opacity: 1, x: 0, scale: 1 }}
                        exit={{ opacity: 0, x: -100, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        className={`absolute inset-0 bg-gradient-to-br ${CARDS[currentIndex].gradient} backdrop-blur-xl rounded-3xl border border-slate-700/50 shadow-2xl p-6 cursor-grab active:cursor-grabbing touch-none`}
                    >
                        {/* Card Header */}
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                {(() => {
                                    const Icon = CARDS[currentIndex].icon;
                                    const color = CARDS[currentIndex].color;
                                    return (
                                        <>
                                            <div className={`p-3 rounded-2xl bg-${color}-500/20 border border-${color}-500/30`}>
                                                <Icon className={`w-6 h-6 text-${color}-400`} />
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-black text-white">{CARDS[currentIndex].title}</h3>
                                                <p className="text-xs text-slate-400 font-mono">Card {currentIndex + 1} of {CARDS.length}</p>
                                            </div>
                                        </>
                                    );
                                })()}
                            </div>
                        </div>

                        {/* Card Content */}
                        <div className="h-[calc(100%-80px)] overflow-hidden">
                            {renderCardContent(CARDS[currentIndex].id)}
                        </div>
                    </motion.div>
                </AnimatePresence>

                {/* Navigation Arrows */}
                <button
                    onClick={goToPrev}
                    disabled={currentIndex === 0}
                    className={`absolute left-4 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-slate-900/80 backdrop-blur-sm border border-slate-700 transition-all ${currentIndex === 0
                        ? 'opacity-30 cursor-not-allowed'
                        : 'hover:bg-slate-800 hover:scale-110 active:scale-95'
                        }`}
                >
                    <ChevronLeft className="w-6 h-6 text-white" />
                </button>

                <button
                    onClick={goToNext}
                    disabled={currentIndex === CARDS.length - 1}
                    className={`absolute right-4 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-slate-900/80 backdrop-blur-sm border border-slate-700 transition-all ${currentIndex === CARDS.length - 1
                        ? 'opacity-30 cursor-not-allowed'
                        : 'hover:bg-slate-800 hover:scale-110 active:scale-95'
                        }`}
                >
                    <ChevronRight className="w-6 h-6 text-white" />
                </button>
            </div>

            {/* Pagination Dots */}
            <div className="flex justify-center gap-2 mt-6">
                {CARDS.map((card, index) => (
                    <button
                        key={card.id}
                        onClick={() => setCurrentIndex(index)}
                        className={`h-2 rounded-full transition-all ${index === currentIndex
                            ? `w-8 bg-${card.color}-500`
                            : 'w-2 bg-slate-600 hover:bg-slate-500'
                            }`}
                    />
                ))}
            </div>

            {/* Swipe Hint */}
            <motion.div
                initial={{ opacity: 1 }}
                animate={{ opacity: currentIndex === 0 ? 1 : 0 }}
                className="absolute bottom-32 left-1/2 -translate-x-1/2 text-xs text-slate-500 font-mono pointer-events-none"
            >
                ← Swipe to explore →
            </motion.div>

            {/* AI Assistant - Floating Button */}
            <CortexChat />
        </div>
    );
};

// 統計卡片組件
const StatCard = ({ label, value, icon: Icon, color }: { label: string; value: string; icon: any; color: string }) => (
    <div className={`bg-slate-800/50 rounded-2xl p-4 border border-${color}-500/20 hover:border-${color}-500/40 transition-all`}>
        <div className="flex items-center justify-between mb-2">
            <Icon className={`w-5 h-5 text-${color}-400`} />
        </div>
        <div className={`text-2xl font-black text-${color}-300 mb-1`}>{value}</div>
        <div className="text-xs text-slate-500 uppercase tracking-wider">{label}</div>
    </div>
);
