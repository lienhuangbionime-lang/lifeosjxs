import React, { useEffect, useState } from 'react';
import { Target, CheckCircle2, FileText, ArrowRight } from 'lucide-react';
import { cortex } from '@/lib/api/client';

interface TodaySnapshotProps {
    logs: any[];
}

export const TodaySnapshot = ({ logs }: TodaySnapshotProps) => {
    const [taskCount, setTaskCount] = useState<number>(0);
    const [focusedProject, setFocusedProject] = useState<string>('No Active Project');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            try {
                // Fetch tasks and count pending
                const tasks = await cortex.getTasks();
                const pendingCount = tasks.filter(t => t.status === 'todo').length;

                // Fetch projects and find the most recently updated active one
                const projects = await cortex.projects.list();
                const activeProjects = projects.filter(p => p.status === 'active');
                if (activeProjects.length > 0) {
                    // Sort by updated_at descending
                    activeProjects.sort((a, b) => {
                        const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
                        const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
                        return dateB - dateA;
                    });
                    if (isMounted) setFocusedProject(activeProjects[0].name);
                }

                if (isMounted) {
                    setTaskCount(pendingCount);
                    setIsLoading(false);
                }
            } catch (err) {
                console.error("Failed to load snapshot data:", err);
                if (isMounted) setIsLoading(false);
            }
        };
        fetchData();
        return () => { isMounted = false; };
    }, []);

    // Get yesterday/latest summary from logs
    const latestLog = logs.length > 0 ? logs[logs.length - 1] : null; // Assuming logs are ascending, if descending take logs[0]
    // Wait, CardStackDashboard sorts them, but props `logs` are normally raw DB entries which might be chronological.
    // Let's sort them to be sure.
    const sortedLogs = [...logs].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    const mostRecent = sortedLogs[0];

    // Extract a 60-char summary snippet
    let summaryText = 'No recent diary entry.';
    if (mostRecent) {
        const rawContent = mostRecent.ai_insights || mostRecent.content || '';
        // Clean markdown
        const plainText = rawContent.replace(/[#*>`[\]_-]/g, '').trim();
        summaryText = plainText.length > 60 ? plainText.substring(0, 60) + '...' : plainText || 'Empty entry.';
    }

    if (isLoading) {
        return (
            <div className="mb-6 h-24 bg-slate-900/50 rounded-2xl border border-slate-800 animate-pulse" />
        );
    }

    return (
        <div className="mb-6 bg-gradient-to-br from-slate-900 to-slate-800/80 rounded-2xl border border-slate-700 p-4 shadow-lg backdrop-blur-md">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                {/* 1. Focused Project */}
                <div className="flex items-start gap-4 p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                    <div className="mt-1 p-2 bg-indigo-500/20 text-indigo-400 rounded-lg">
                        <Target size={18} />
                    </div>
                    <div>
                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Focus Project</h4>
                        <p className="font-bold text-indigo-300 text-sm">{focusedProject}</p>
                    </div>
                </div>

                {/* 2. Yesterday Summary */}
                <div className="flex items-start gap-4 p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 md:col-span-1">
                    <div className="mt-1 p-2 bg-emerald-500/20 text-emerald-400 rounded-lg">
                        <FileText size={18} />
                    </div>
                    <div className="overflow-hidden">
                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Latest Log</h4>
                        <p className="text-slate-300 text-xs leading-relaxed truncate-2-lines">{summaryText}</p>
                    </div>
                </div>

                {/* 3. Pending Tasks */}
                <div className="flex items-start gap-4 p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                    <div className="mt-1 p-2 bg-amber-500/20 text-amber-400 rounded-lg">
                        <CheckCircle2 size={18} />
                    </div>
                    <div className="flex-1">
                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Action Items</h4>
                        <div className="flex items-baseline gap-2">
                            <span className="text-xl font-black text-amber-300">{taskCount}</span>
                            <span className="text-xs text-slate-400 font-medium">Pending Tasks</span>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};
