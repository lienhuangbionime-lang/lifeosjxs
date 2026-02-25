'use client';
import React, { useEffect, useState, useRef } from 'react';
import { X, Zap, BookOpen, Brain, CheckSquare, Circle, Loader2, ExternalLink, GitMerge, Edit2, Check, Network } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Project } from '@/lib/types/api-schema';
import { TaskList } from './TaskList';

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
    onJumpToGraph?: (projectName: string) => void;
}

interface RelatedMemory {
    id: string;
    date: string;
    content: string;
    mood?: number;
}

function SimpleMd({ text }: { text: string }) {
    if (!text) return <p className="text-slate-600 italic text-sm">尚無說明。點擊「編輯」加入...</p>;

    const renderText = (str: string) => {
        // Handle **bold**
        const parts = str.split(/(\*\*.*?\*\*)/g);
        return parts.map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <span key={i} className="font-bold text-white/90">{part.slice(2, -2)}</span>;
            }
            return part;
        });
    };

    const lines = text.split('\n');
    return (
        <div className="space-y-1.5">
            {lines.map((line, i) => {
                const trimmed = line.trim();
                if (!trimmed) return <div key={i} className="h-2" />;

                // Headers
                if (line.startsWith('### ')) return <p key={i} className="text-sm font-bold text-slate-200 mt-3">{renderText(line.slice(4))}</p>;
                if (line.startsWith('## ')) return <p key={i} className="text-base font-black text-white mt-4">{renderText(line.slice(3))}</p>;
                if (line.startsWith('# ')) return <p key={i} className="text-lg font-black text-white mt-4">{renderText(line.slice(2))}</p>;

                // Lists
                if (line.startsWith('- ')) {
                    return (
                        <div key={i} className="flex gap-2 text-sm text-slate-400 pl-1">
                            <span className="text-slate-600 mt-1.5 shrink-0">•</span>
                            <span className="leading-relaxed">{renderText(line.slice(2))}</span>
                        </div>
                    );
                }

                // Numbered Lists (1. Content)
                const numMatch = line.match(/^(\d+\.)\s+(.*)/);
                if (numMatch) {
                    return (
                        <div key={i} className="flex gap-2 text-sm text-slate-400 pl-1 mt-1">
                            <span className="font-black text-violet-400 shrink-0 min-w-[20px]">{numMatch[1]}</span>
                            <span className="leading-relaxed">{renderText(numMatch[2])}</span>
                        </div>
                    );
                }

                return <p key={i} className="text-sm text-slate-400 leading-relaxed">{renderText(line)}</p>;
            })}
        </div>
    );
}

export const ProjectDetailPanel = ({ project, onClose, onUpdate, onJumpToGraph }: ProjectDetailPanelProps) => {
    const [memories, setMemories] = useState<RelatedMemory[]>([]);
    const [insight, setInsight] = useState<string>('');
    const [loadingMemories, setLoadingMemories] = useState(false);
    const [loadingInsight, setLoadingInsight] = useState(false);
    const [editingProgress, setEditingProgress] = useState(false);
    const [progressVal, setProgressVal] = useState(0);
    const [editingDesc, setEditingDesc] = useState(false);
    const [descVal, setDescVal] = useState('');
    const [allProjects, setAllProjects] = useState<Project[]>([]);
    const [mergeTarget, setMergeTarget] = useState('');
    const [showMerge, setShowMerge] = useState(false);
    const [merging, setMerging] = useState(false);
    const panelRef = useRef<HTMLDivElement>(null);

    const status = project?.status || 'active';
    const cfg = STATUS_CONFIG[status] || STATUS_CONFIG['active'];
    const progress = project?.progress ?? 0;

    useEffect(() => {
        if (!project) return;
        setProgressVal(project.progress ?? 0);
        setDescVal(project.description || '');
        setMemories([]);
        setInsight('');
        setShowMerge(false);

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

        // Load all projects for merge dropdown
        const loadProjects = async () => {
            try {
                const { cortex } = await import('@/lib/api/client');
                const data = await cortex.projects.list();
                setAllProjects((data || []).filter((p: Project) => p.id !== project.id && p.status !== 'archived'));
            } catch { }
        };
        loadProjects();
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

    const handleDescSave = () => {
        if (project) onUpdate(project.id, { description: descVal });
        setEditingDesc(false);
    };

    const handleMerge = async () => {
        if (!mergeTarget || !project) return;
        setMerging(true);
        try {
            const { cortex } = await import('@/lib/api/client');
            await cortex.projects.merge(project.id, mergeTarget);
            alert(`已合併！此專案的任務已轉移到目標專案。`);
            onClose();
        } catch (e) {
            alert('合併失敗，請稍後再試。');
        } finally {
            setMerging(false);
        }
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
                        <div className="flex gap-1 shrink-0">
                            {onJumpToGraph && (
                                <button onClick={() => onJumpToGraph(project.name)}
                                    title="View in Brain Graph"
                                    className="p-2 text-indigo-400 hover:text-white hover:bg-indigo-500/20 rounded-full transition-all shrink-0">
                                    <Network size={18} />
                                </button>
                            )}
                            <button onClick={onClose}
                                className="p-2 text-slate-500 hover:text-white hover:bg-white/10 rounded-full transition-all shrink-0">
                                <X size={18} />
                            </button>
                        </div>
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
                            {!editingDesc && (
                                <button onClick={() => setEditingDesc(true)}
                                    className="ml-auto text-[9px] text-slate-500 hover:text-white flex items-center gap-1">
                                    <Edit2 size={9} /> 編輯
                                </button>
                            )}
                        </h3>
                        {editingDesc ? (
                            <div className="space-y-2">
                                <textarea
                                    value={descVal}
                                    onChange={e => setDescVal(e.target.value)}
                                    rows={6}
                                    autoFocus
                                    className="w-full bg-white/5 border border-cyan-500 text-slate-200 text-sm rounded-xl p-3 outline-none resize-none font-mono"
                                    placeholder="說明這個專案的目標、背景、里程碑..."
                                />
                                <div className="flex gap-2">
                                    <button onClick={handleDescSave}
                                        className="flex items-center gap-1 px-3 py-1.5 bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-lg text-xs font-bold hover:bg-cyan-500/30">
                                        <Check size={11} /> 儲存
                                    </button>
                                    <button onClick={() => { setEditingDesc(false); setDescVal(project?.description || ''); }}
                                        className="px-3 py-1.5 text-slate-500 text-xs rounded-lg hover:bg-white/5">取消</button>
                                </div>
                            </div>
                        ) : (
                            <div onClick={() => setEditingDesc(true)} className="cursor-pointer">
                                <SimpleMd text={project.description || ''} />
                            </div>
                        )}
                    </section>

                    {/* Task List */}
                    <section>
                        <TaskList projectId={project.id} />
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
                                <SimpleMd text={insight} />
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

                    {/* Merge */}
                    <section>
                        <h3 className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <GitMerge size={11} /> 合併到另一個專案
                        </h3>
                        {!showMerge ? (
                            <button onClick={() => setShowMerge(true)}
                                className="text-xs text-slate-500 hover:text-amber-400 border border-white/8 rounded-lg px-3 py-1.5 transition-colors">
                                合併此專案...
                            </button>
                        ) : (
                            <div className="space-y-2">
                                <select
                                    value={mergeTarget}
                                    onChange={e => setMergeTarget(e.target.value)}
                                    className="w-full bg-white/5 border border-amber-500/30 text-slate-300 text-sm rounded-xl px-3 py-2 outline-none">
                                    <option value="">選擇目標專案...</option>
                                    {allProjects.map(p => (
                                        <option key={p.id} value={p.id}>{p.name}</option>
                                    ))}
                                </select>
                                <p className="text-[10px] text-slate-500">合併後，此專案的任務和 Brain 連線將移到目標專案，此專案將標記為 Archived。</p>
                                <div className="flex gap-2">
                                    <button onClick={handleMerge} disabled={!mergeTarget || merging}
                                        className="flex items-center gap-1 px-3 py-1.5 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg text-xs font-bold disabled:opacity-40">
                                        {merging ? <Loader2 size={11} className="animate-spin" /> : <GitMerge size={11} />} 確認合併
                                    </button>
                                    <button onClick={() => setShowMerge(false)} className="px-3 py-1.5 text-slate-500 text-xs rounded-lg hover:bg-white/5">取消</button>
                                </div>
                            </div>
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
