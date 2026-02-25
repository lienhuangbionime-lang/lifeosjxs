'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import {
    Activity, Rocket, Hash, TrendingUp,
    Calendar, ChevronLeft, ChevronRight, Sparkles, Brain, CheckCircle2
} from 'lucide-react';
import {
    ComposedChart, Area, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { NEON_PALETTE } from '@/lib/ai/core';
import { CortexChat } from './CortexChat';
import { TodaySnapshot } from './TodaySnapshot';

import { ReviewCard } from './ReviewCard';

interface CardStackDashboardProps {
    logs?: any[];
    onNavigate?: (tab: string, param?: string) => void;
}

// 定義卡片類型
type CardType = 'overview' | 'tags' | 'reflection' | 'review';

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
        id: 'tags',
        title: 'Neural Tags',
        icon: Hash,
        color: 'violet',
        gradient: 'from-violet-500/20 to-fuchsia-500/20'
    },
    {
        id: 'reflection',
        title: 'Subconscious Insights',
        icon: Sparkles,
        color: 'teal',
        gradient: 'from-teal-500/20 to-emerald-500/20'
    },
    {
        id: 'review',
        title: 'Monthly Review',
        icon: Sparkles,
        color: 'amber',
        gradient: 'from-amber-500/20 to-orange-500/20'
    },
];

export const CardStackDashboard = ({ logs = [], onNavigate }: CardStackDashboardProps) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [dashboardMonth, setDashboardMonth] = useState(new Date().toISOString().slice(0, 7));

    // Smart Default: If current month has no data, jump to last active month
    React.useEffect(() => {
        if (logs.length > 0) {
            const currentMonth = new Date().toISOString().slice(0, 7);
            const hasDataForCurrent = logs.some(l => l.date && l.date.startsWith(currentMonth));

            if (!hasDataForCurrent) {
                // Find latest valid date
                const latestLog = logs.reduce((latest: any, current: any) => {
                    if (!latest || (current.date && current.date > latest.date)) return current;
                    return latest;
                }, null);

                if (latestLog && latestLog.date) {
                    const latestMonth = latestLog.date.slice(0, 7);
                    if (latestMonth !== dashboardMonth) {
                        setDashboardMonth(latestMonth);
                    }
                }
            }
        }
    }, [logs]);

    const [isReflecting, setIsReflecting] = useState(false);
    const [insightText, setInsightText] = useState<string | null>(null);
    const [allTasks, setAllTasks] = useState<any[]>([]);

    React.useEffect(() => {
        const loadMetaData = async () => {
            try {
                const { cortex } = await import('@/lib/api/client');
                const t = await cortex.getTasks();
                if (Array.isArray(t)) setAllTasks(t);
            } catch (e) {
                console.error("Failed to load tasks for dashboard", e);
            }
        };
        loadMetaData();
    }, []);

    const triggerReflection = async () => {
        setIsReflecting(true);
        try {
            const { cortex } = await import('@/lib/api/client');
            const data = await cortex.subconscious.reflect();
            if (data.success && data.data) {
                setInsightText(data.data.content);
                alert("New Insight Generated!");
            } else {
                alert(data.message || "Failed to generate insight.");
            }
        } catch (error) {
            console.error(error);
            alert("Error triggering subconscious reflection.");
        } finally {
            setIsReflecting(false);
        }
    };

    // 處理數據
    const processedData = React.useMemo(() => {
        const filtered = logs.filter(l => l.date?.startsWith(dashboardMonth));
        const sorted = filtered.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        // Tag Cloud — gather from all logs this month across tags DB column OR parsed from markdown
        const tagsMap = new Map<string, number>();
        sorted.forEach(l => {
            // Prefer the DB tags array
            const dbTags: string[] = Array.isArray(l.tags) ? l.tags : [];
            // Fallback: parse hashtags from note or ai_insights markdown
            const rawText = l.note || l.ai_insights || '';
            const parsedTags: string[] = dbTags.length > 0
                ? []
                : (rawText.match(/#([\w\u4e00-\u9fa5]+)/g) || []).map((t: string) => t.slice(1));
            const allTags = [...dbTags, ...parsedTags];
            allTags.forEach((t: string) => tagsMap.set(t, (tagsMap.get(t) || 0) + 1));
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

        const completedTasksThisMonth = allTasks.filter(t =>
            t.status === 'done' &&
            t.updated_at &&
            t.updated_at.startsWith(dashboardMonth)
        ).length;

        return { chartData: sorted, tagCloud, totalEntries, avgMood, totalDeepWork, completedTasksThisMonth };
    }, [logs, dashboardMonth, allTasks]);

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
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-3">
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
                                label="Tasks Done"
                                value={processedData.completedTasksThisMonth.toString()}
                                icon={CheckCircle2}
                                color="cyan"
                            />
                            <StatCard
                                label="Deep Work"
                                value={`${Math.floor(processedData.totalDeepWork / 60)}h`}
                                icon={Rocket}
                                color="pink"
                            />
                        </div>

                        {processedData.chartData.length > 0 ? (
                            <div className="bg-slate-900/60 rounded-2xl p-4 border border-slate-700/50">
                                <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest mb-3 flex items-center gap-2">
                                    <TrendingUp className="w-3 h-3 text-indigo-400" /> Mood · Focus · Energy
                                </p>
                                <ResponsiveContainer width="100%" height={160}>
                                    <ComposedChart data={processedData.chartData} margin={{ top: 0, right: 0, bottom: 0, left: -34 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 9 }} tickFormatter={(v: string) => v?.slice(5) || ''} />
                                        <YAxis domain={[0, 10]} tick={{ fill: '#64748b', fontSize: 9 }} />
                                        <Tooltip
                                            contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 12, fontSize: 11 }}
                                            labelStyle={{ color: '#94a3b8' }}
                                        />
                                        <Area type="monotone" dataKey="metrics.mood" fill="#6366f155" stroke="#6366f1" strokeWidth={2} name="Mood" dot={false} />
                                        <Line type="monotone" dataKey="metrics.focus" stroke="#10b981" strokeWidth={2} name="Focus" dot={false} />
                                        <Line type="monotone" dataKey="metrics.energy" stroke="#f59e0b" strokeWidth={2} name="Energy" dot={false} strokeDasharray="4 2" />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/50 flex flex-col items-center justify-center text-center h-36">
                                <Activity className="w-8 h-8 text-indigo-500/50 mb-3" />
                                <p className="text-xs text-slate-500">這個月尚無日記資料</p>
                            </div>
                        )}
                    </div>
                );

            case 'reflection':
                // Find latest reflection in memory for this month if exists
                const latestReflection = [...logs]
                    .filter(l => l.type === 'reflection')
                    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())[0];

                const displayIdea = insightText || (latestReflection ? latestReflection.content : "The subconscious is quiet. Awaiting enough experiences to form a profound insight.");

                return (
                    <div className="h-full flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <h4 className="text-sm font-bold text-slate-300 flex items-center gap-2">
                                <Sparkles className="w-4 h-4 text-teal-400" />
                                Subconscious Synthesis
                            </h4>
                            <button
                                onClick={triggerReflection}
                                disabled={isReflecting}
                                className="px-3 py-1 bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/20 rounded-lg text-xs font-bold transition-all disabled:opacity-50"
                            >
                                {isReflecting ? "Reflecting..." : "Force Reflection"}
                            </button>
                        </div>

                        <div className={`flex-1 bg-slate-900/60 rounded-3xl p-8 border border-slate-700/50 overflow-y-auto custom-scrollbar ${isReflecting ? 'animate-pulse' : ''}`}>
                            {isReflecting ? (
                                <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
                                    <Brain className="w-12 h-12 text-teal-500/50 animate-bounce" />
                                    <p className="font-mono text-sm">Processing recent memories into deep insights...</p>
                                </div>
                            ) : (
                                <div className="prose prose-invert prose-teal max-w-none text-slate-200 leading-relaxed text-lg"
                                    dangerouslySetInnerHTML={{ __html: displayIdea.replace(/\n/g, '<br/>') }}
                                />
                            )}
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
                                        onClick={() => onNavigate && onNavigate('graph', tag.name)}
                                        className="flex items-center gap-1.5 bg-slate-800/80 px-3 py-2 rounded-xl border border-violet-500/30 hover:border-violet-400/50 transition-colors cursor-pointer hover:bg-violet-500/10"
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

            case 'review':
                return (
                    <div className="h-full">
                        <ReviewCard month={dashboardMonth} />
                    </div>
                );

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
