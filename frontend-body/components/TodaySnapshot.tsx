'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
    Sun,
    CheckCircle2,
    Target,
    Loader2,
    TrendingUp,
    Brain,
    Zap,
    Activity
} from 'lucide-react';
import { cortex, LogEntry } from '@/lib/api/client';
import { Project } from '@/lib/types/api-schema';

interface TodaySnapshotData {
    latestMemory: LogEntry | null;
    pendingTasksCount: number;
    focusedProject: Project | null;
    focusedProjectTasks: any[];
}

const getRelativeTime = (dateStr?: string) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} days ago`;
    if (hours > 0) return `${hours} hours ago`;
    if (minutes > 0) return `${minutes} minutes ago`;
    return 'Just now';
};

export const TodaySnapshot = () => {
    const [data, setData] = useState<TodaySnapshotData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;

        const fetchSnapshotData = async () => {
            try {
                setLoading(true);

                // Fetch recent memory
                const memories = await cortex.getRecentMemories(1);
                const latestMemory = memories.length > 0 ? memories[0] : null;

                // Fetch active tasks
                // Assuming cortex.getTasks returns tasks, we filter for "todo"
                const tasks = await cortex.getTasks();
                const pendingTasksCount = Array.isArray(tasks)
                    ? tasks.filter((t: any) => t.status === 'todo').length
                    : 0;

                // Fetch projects and find the most recently updated active one
                const projects = await cortex.projects.list();
                const activeProjects = Array.isArray(projects)
                    ? projects.filter((p: Project) => p.status === 'active')
                    : [];

                // Sort by updated_at descending
                activeProjects.sort((a, b) => {
                    const dateA = new Date(a.updated_at || 0).getTime();
                    const dateB = new Date(b.updated_at || 0).getTime();
                    return dateB - dateA;
                });

                const focusedProject = activeProjects.length > 0 ? activeProjects[0] : null;

                // Extract tasks for that focused project
                const focusedProjectTasks = focusedProject && Array.isArray(tasks)
                    ? tasks.filter((t: any) => t.status === 'todo' && t.project_id === focusedProject.id).slice(0, 2)
                    : [];

                if (mounted) {
                    setData({
                        latestMemory,
                        pendingTasksCount,
                        focusedProject,
                        focusedProjectTasks
                    });
                }
            } catch (err) {
                console.error("Failed to fetch TodaySnapshot data", err);
            } finally {
                if (mounted) setLoading(false);
            }
        };

        fetchSnapshotData();

        return () => {
            mounted = false;
        };
    }, []);

    if (loading) {
        return (
            <div className="w-full bg-[#111] border border-white/5 rounded-2xl p-6 flex flex-col justify-center items-center py-12">
                <Loader2 className="animate-spin text-slate-600 mb-3" size={24} />
                <p className="text-xs text-slate-500 font-medium uppercase tracking-widest">
                    Syncing Cortex...
                </p>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
        >
            {/* 1. Yesterday's / Latest Abstract */}
            <div className="bg-[#111] border border-white/10 rounded-2xl p-5 relative overflow-hidden group hover:border-white/20 transition-all flex flex-col justify-between">
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-violet-500/10 rounded-full blur-2xl group-hover:bg-violet-500/20 transition-all" />

                <div>
                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                        <Brain size={12} className="text-violet-400" />
                        LATEST MEMORY
                    </h3>

                    <div className="mb-4">
                        {data?.latestMemory ? (
                            <div>
                                <p className="text-sm text-slate-300 leading-relaxed line-clamp-3">
                                    {data.latestMemory.content?.replace(/[#*`]/g, '') || "No content."}
                                </p>
                                <span className="text-[10px] text-slate-600 font-mono mt-2 block">
                                    {data.latestMemory.date}
                                </span>
                            </div>
                        ) : (
                            <p className="text-xs text-slate-600 italic">No recent memories found.</p>
                        )}
                    </div>
                </div>

                {data?.latestMemory && (
                    <div className="flex items-center gap-3 pt-3 border-t border-white/5">
                        <div className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md">
                            <Activity size={10} /> Mood {data.latestMemory.mood || '-'}
                        </div>
                        <div className="flex items-center gap-1 text-[11px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-md">
                            <Target size={10} /> Focus {data.latestMemory.focus || '-'}
                        </div>
                        <div className="flex items-center gap-1 text-[11px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-md">
                            <Zap size={10} /> Energy {data.latestMemory.energy || '-'}
                        </div>
                    </div>
                )}
            </div>

            {/* 2. Tasks / Action Summary */}
            <div className="bg-[#111] border border-white/10 rounded-2xl p-5 relative overflow-hidden group hover:border-emerald-500/20 transition-all flex flex-col justify-between">
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all" />

                <div>
                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                        <CheckCircle2 size={12} className="text-emerald-400" />
                        PENDING TASKS
                    </h3>

                    <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-black text-white tracking-tighter">
                            {data?.pendingTasksCount || 0}
                        </span>
                        <span className="text-xs text-slate-500 font-medium">actionable items</span>
                    </div>
                </div>

                <p className="text-xs text-slate-500 leading-relaxed mt-4">
                    Tasks mentioned in notes or linked to active projects waiting for execution.
                </p>
            </div>

            {/* 3. Focused Project */}
            <div className="bg-[#111] border border-white/10 rounded-2xl p-5 relative overflow-hidden group hover:border-cyan-500/20 transition-all flex flex-col justify-between">
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-cyan-500/10 rounded-full blur-2xl group-hover:bg-cyan-500/20 transition-all" />

                <div>
                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                        <TrendingUp size={12} className="text-cyan-400" />
                        FOCUSED PROJECT
                    </h3>

                    {data?.focusedProject ? (
                        <div>
                            <div className="flex items-center gap-2 mb-2">
                                {data.focusedProject.meta?.emoji && (
                                    <span className="text-xl">{data.focusedProject.meta.emoji}</span>
                                )}
                                <h4 className="text-lg font-black text-white tracking-tight leading-tight truncate">
                                    {data.focusedProject.name}
                                </h4>
                            </div>

                            <div className="mt-3 space-y-1.5">
                                <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                    <span>進度 (Progress)</span>
                                    <span className="text-cyan-400">{data.focusedProject.progress || 0}%</span>
                                </div>
                                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                    <motion.div
                                        className="h-full bg-cyan-500 rounded-full relative"
                                        initial={{ width: 0 }}
                                        animate={{ width: `${data.focusedProject.progress || 0}%` }}
                                        transition={{ duration: 1, ease: "easeOut" }}
                                    >
                                        <div className="absolute inset-0 bg-white/20" style={{ backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.15) 50%, rgba(255,255,255,.15) 75%, transparent 75%, transparent)' }} />
                                    </motion.div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <p className="text-xs text-slate-600 italic mt-2">No active projects currently.</p>
                    )}

                    {/* FOCUSED ACTION ITEMS */}
                    {data?.focusedProjectTasks && data.focusedProjectTasks.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-white/5">
                            <h4 className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1">
                                <Target size={10} className="text-emerald-400" /> NEXT ACTIONS
                            </h4>
                            <div className="space-y-1.5">
                                {data.focusedProjectTasks.map(t => (
                                    <div key={t.id} className="text-xs text-slate-300 flex items-start gap-1.5">
                                        <div className="mt-0.5 w-1 h-1 rounded-full bg-emerald-500 shrink-0" />
                                        <span className="line-clamp-1">{t.title}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {data?.focusedProject && (
                    <div className="flex justify-between items-center text-xs text-slate-500 mt-4 border-t border-white/5 pt-3">
                        <span>Active project</span>
                        <span className="text-cyan-500/80 font-mono">
                            {data.focusedProject.updated_at
                                ? `Updated ${getRelativeTime(data.focusedProject.updated_at)}`
                                : ''}
                        </span>
                    </div>
                )}
            </div>

        </motion.div>
    );
};
