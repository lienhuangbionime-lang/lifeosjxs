'use client';
import React, { useEffect, useState, useRef } from 'react';
import { X, Zap, BookOpen, Brain, CheckSquare, Circle, Loader2, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Project } from '@/lib/types/api-schema';

const STATUS_CONFIG: Record<string, { label: string; color: string; bar: string; bg: string }> = {
    active: { label: 'ACTIVE', color: 'text-cyan-400', bar: 'bg-cyan-500', bg: 'bg-cyan-500/10' },
    idea: { label: 'IDEA', color: 'text-violet-400', bar: 'bg-violet-500', bg: 'bg-violet-500/10' },
    on_hold: { label: 'ON HOLD', color: 'text-amber-400', bar: 'bg-amber-500', bg: 'bg-amber-500/10' },
    completed: { label: 'DONE', color: 'text-emerald-400', bar: 'bg-emerald-500', bg: 'bg-emerald-500/10' },
    archived: { label: 'ARCHIVED', color: 'text-slate-500', bar: 'bg-slate-600', bg: 'bg-slate-500/10' },
};

interface ProjectDetailPanelProps {
    project: Project | null;
    onClose: () => void;
    onUpdate: (id: string, data: Partial<Project>) => void;
}

interface RelatedMemory {
    id: string;
    date: string;
    content: string;
    mood?: number;
}

function SimpleMd({ text }: { text: string }) {
    if (!text) return <p className="text-slate-600 italic text-sm">尚無說明。點擊「編輯」加入...</p>;
    // Very light render — bold+newlines
    const lines = text.split('\n');
    return (
        <div className="space-y-1.5">
            {lines.map((line, i) => {
                if (line.startsWith('### ')) return <p key={i} className="text-sm font-bold text-slate-200 mt-3">{line.slice(4)}</p>;
                if (line.startsWith('## ')) return <p key={i} className="text-base font-black text-white mt-4">{line.slice(3)}</p>;
                if (line.startsWith('# ')) return <p key={i} className="text-lg font-black text-white mt-4">{line.slice(2)}</p>;
                if (line.startsWith('- ')) return <p key={i} className="text-sm text-slate-400 pl-3 before:content-['—'] before:mr-2 before:text-slate-600">{line.slice(2)}</p>;
                if (line.trim() === '') return <div key={i} className="h-2" />;
                return <p key={i} className="text-sm text-slate-400 leading-relaxed">{line}</p>;
            })}
        </div>
    );
}

export const ProjectDetailPanel = ({ project, onClose, onUpdate }: ProjectDetailPanelProps) => {
    const [memories, setMemories] = useState<RelatedMemory[]>([]);
    const [insight, setInsight] = useState<string>('');
    const [loadingMemories, setLoadingMemories] = useState(false);
    const [loadingInsight, setLoadingInsight] = useState(false);
    const [editingProgress, setEditingProgress] = useState(false);
    const [progressVal, setProgressVal] = useState(0);
    const panelRef = useRef<HTMLDivElement>(null);

    const status = project?.status || 'active';
    const cfg = STATUS_CONFIG[status] || STATUS_CONFIG['active'];
    const progress = project?.progress ?? 0;

    useEffect(() => {
        if (!project) return;
        setProgressVal(project.progress ?? 0);
        setMemories([]);
        setInsight('');

        // Fetch related memories
        const fetchContext = async () => {
            setLoadingMemories(true);
            try {
                const { cortex } = await import('@/lib/api/client');
                const data = await cortex.brain.getNodeContext(project.name);
                if (Array.isArray(data)) setMemories(data.slice(0, 5));
            } catch (e) {
                console.warn('Could not load related memories', e);
            }
            setLoadingMemories(false);
        };

        // Fetch AI insight
        const fetchInsight = async () => {
            setLoadingInsight(true);
            try {
                const { cortex } = await import('@/lib/api/client');
                const data = await cortex.brain.getNodeInsight(project.name);
                if (data?.insight) setInsight(data.insight);
            } catch (e) {
                console.warn('Could not load AI insight', e);
            }
            setLoadingInsight(false);
        };

        fetchContext();
        fetchInsight();
    }, [project?.id]);

    // Click outside to close
    useEffect(() => {
        const handle = (e: MouseEvent) => {
            if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
                onClose();
            }
        };
        document.addEventListener('mousedown', handle);
        return () => document.removeEventListener('mousedown', handle);
    }, [onClose]);

    const handleProgressSave = () => {
        if (project) onUpdate(project.id, { progress: progressVal });
        setEditingProgress(false);
    };

    if (!project) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
            <motion.div
                ref={panelRef}
                initial={{ x: '100%', opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: '100%', opacity: 0 }}
                transition={{ type: 'spring', damping: 28, stiffness: 280 }}
                className="fixed right-0 top-0 h-full w-full max-w-[520px] z-50 bg-[#0a0a0a] border-l border-white/10 flex flex-col shadow-2xl overflow-hidden"
            >
                {/* ── Top Status Bar ── */}
                <div className={`h-1 w-full ${cfg.bar}`} />

                {/* ── Header ── */}
                <div className="p-6 pb-4 border-b border-white/8">
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                            <div className={`text-[10px] font-black tracking-widest uppercase mb-1.5 ${cfg.color}`}>
                                {project.meta?.emoji && <span className="mr-1.5">{project.meta.emoji}</span>}
                                {cfg.label}
                            </div>
                            <h2 className="text-2xl font-black text-white tracking-tight leading-tight">
                                {project.name}
                            </h2>
                        </div>
                        <button onClick={onClose}
                            className="p-2 text-slate-500 hover:text-white hover:bg-white/10 rounded-full transition-all shrink-0">
                            <X size={18} />
                        </button>
                    </div>

                    {/* Progress */}
                    <div className="mt-4 space-y-2">
                        <div className="flex justify-between items-center">
                            <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">進度</span>
                            {editingProgress ? (
                                <div className="flex items-center gap-2">
                                    <input
                                        type="number" min={0} max={100}
                                        value={progressVal}
                                        onChange={e => setProgressVal(Number(e.target.value))}
                                        onBlur={handleProgressSave}
                                        onKeyDown={e => e.key === 'Enter' && handleProgressSave()}
                                        autoFocus
                                        className="w-16 text-right text-sm font-black bg-white/5 border border-cyan-500 text-cyan-400 rounded px-2 py-0.5 outline-none"
                                    />
                                    <span className={`text-sm font-black ${cfg.color}`}>%</span>
                                </div>
                            ) : (
                                <button onClick={() => setEditingProgress(true)}
                                    className={`text-xl font-black tabular-nums ${cfg.color} hover:underline`}>
                                    {progress}%
                                </button>
                            )}
                        </div>
                        <div className="h-3 w-full bg-white/5 rounded-full overflow-hidden">
                            <motion.div
                                className={`h-full rounded-full ${cfg.bar}`}
                                animate={{ width: `${progress}%` }}
                                transition={{ duration: 0.8, ease: 'easeOut' }}
                            />
                        </div>
                    </div>
                </div>

                {/* ── Scrollable content ── */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10">

                    {/* Description */}
                    <section>
                        <h3 className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <BookOpen size={11} /> 說明
                        </h3>
                        <SimpleMd text={project.description || ''} />
                    </section>

                    {/* AI Insight */}
                    <section>
                        <h3 className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <Brain size={11} className="text-violet-400" /> AI 洞察
                        </h3>
                        {loadingInsight ? (
                            <div className="flex items-center gap-2 text-slate-600">
                                <Loader2 size={12} className="animate-spin" />
                                <span className="text-xs">分析中...</span>
                            </div>
                        ) : insight ? (
                            <div className="bg-violet-500/10 border border-violet-500/20 rounded-xl p-4">
                                <p className="text-sm text-violet-300 leading-relaxed">{insight}</p>
                            </div>
                        ) : (
                            <p className="text-xs text-slate-600 italic">尚無 AI 洞察（需要更多日記資料）</p>
                        )}
                    </section>

                    {/* Related Memories */}
                    <section>
                        <h3 className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <Zap size={11} className="text-amber-400" /> 相關日記
                        </h3>
                        {loadingMemories ? (
                            <div className="flex items-center gap-2 text-slate-600">
                                <Loader2 size={12} className="animate-spin" />
                                <span className="text-xs">搜尋關聯記憶...</span>
                            </div>
                        ) : memories.length > 0 ? (
                            <div className="space-y-2">
                                {memories.map((m) => (
                                    <div key={m.id}
                                        className="bg-white/3 border border-white/8 rounded-xl p-3 hover:border-white/15 transition-colors group">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-[10px] font-bold text-slate-500 font-mono">{m.date}</span>
                                            {m.mood !== undefined && (
                                                <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold ${m.mood >= 7 ? 'bg-emerald-500/20 text-emerald-400' : m.mood <= 4 ? 'bg-red-500/20 text-red-400' : 'bg-slate-500/20 text-slate-400'}`}>
                                                    ♡ {m.mood}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                                            {(m.content || '').replace(/[#*\[\]`>]/g, '').slice(0, 160)}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-xs text-slate-600 italic">找不到相關日記（試著把專案名稱寫進日記）</p>
                        )}
                    </section>

                    {/* Status switcher */}
                    <section>
                        <h3 className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <CheckSquare size={11} /> 狀態
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(STATUS_CONFIG).map(([key, val]) => (
                                <button
                                    key={key}
                                    onClick={() => onUpdate(project.id, { status: key as any })}
                                    className={`px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-wider transition-all border
                                        ${status === key
                                            ? `${val.bg} ${val.color} border-current`
                                            : 'bg-white/3 text-slate-500 border-white/10 hover:border-white/20'
                                        }`}
                                >
                                    {val.label}
                                </button>
                            ))}
                        </div>
                    </section>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};
