'use client';
import React, { useState, useRef, useEffect } from 'react';
import { MoreHorizontal, Trash2, Edit2, GitMerge, CheckCircle, Calendar, CheckSquare, Zap, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Project } from '@/lib/types/api-schema';

interface ProjectCardProps {
    project: Project;
    isSelectionMode: boolean;
    isSelected: boolean;
    onSelect: (id: string) => void;
    onUpdate: (id: string, data: Partial<Project>) => void;
    onDelete: (id: string) => void;
    onOpen: (project: Project) => void;
    onDragStart?: (e: React.DragEvent, id: string) => void;
    onDrop?: (e: React.DragEvent, targetId: string) => void;
}

// Status config — Nomads.com clarity
const STATUS_CONFIG: Record<string, { label: string; color: string; bar: string; dot: string }> = {
    active: { label: 'ACTIVE', color: 'text-cyan-400', bar: 'bg-cyan-500', dot: 'bg-cyan-400' },
    idea: { label: 'IDEA', color: 'text-violet-400', bar: 'bg-violet-500', dot: 'bg-violet-400' },
    on_hold: { label: 'ON HOLD', color: 'text-amber-400', bar: 'bg-amber-500', dot: 'bg-amber-400' },
    completed: { label: 'DONE', color: 'text-emerald-400', bar: 'bg-emerald-500', dot: 'bg-emerald-400' },
    archived: { label: 'ARCHIVED', color: 'text-slate-500', bar: 'bg-slate-600', dot: 'bg-slate-500' },
};

function getLastActive(project: Project): string {
    const date = project.updated_at || project.created_at;
    if (!date) return '—';
    const diff = Math.floor((Date.now() - new Date(date).getTime()) / 86400000);
    if (diff === 0) return 'Today';
    if (diff === 1) return '1d ago';
    return `${diff}d ago`;
}

function getVibeLabel(progress: number, status: string): string {
    if (status === 'completed') return '完成 ✓';
    if (status === 'idea') return '構想中';
    if (progress >= 80) return '衝刺 🔥';
    if (progress >= 50) return '進行中';
    if (progress >= 20) return '起步';
    return '剛開始';
}

export const ProjectCard = ({
    project, isSelectionMode, isSelected, onSelect,
    onUpdate, onDelete, onOpen, onDragStart, onDrop
}: ProjectCardProps) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editName, setEditName] = useState(project.name);
    const [showMenu, setShowMenu] = useState(false);
    const [isTargeted, setIsTargeted] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const status = project.status || 'active';
    const cfg = STATUS_CONFIG[status] || STATUS_CONFIG['active'];
    const progress = project.progress ?? 0;
    const teaser = project.description
        ? project.description.replace(/[#*\[\]`>]/g, '').slice(0, 72)
        : '點擊查看詳情 →';

    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [isEditing]);

    const handleRename = () => {
        if (editName.trim() && editName !== project.name)
            onUpdate(project.id, { name: editName });
        setIsEditing(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleRename();
        if (e.key === 'Escape') { setEditName(project.name); setIsEditing(false); }
    };

    const handleCardClick = (e: React.MouseEvent) => {
        if (isEditing || showMenu) return;
        if (isSelectionMode) { onSelect(project.id); return; }
        onOpen(project);
    };

    // DnD
    const handleDragEnter = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsTargeted(true); };
    const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsTargeted(false); };
    const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); };
    const handleDropInternal = (e: React.DragEvent) => {
        e.preventDefault(); e.stopPropagation();
        setIsTargeted(false);
        if (onDrop) onDrop(e, project.id);
    };

    return (
        <motion.div
            draggable={!isEditing && !isSelectionMode}
            onDragStart={(e) => onDragStart && onDragStart(e as any, project.id)}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDropInternal}
            onClick={handleCardClick}
            whileHover={{ y: -3, transition: { duration: 0.2 } }}
            className={`
                relative overflow-hidden rounded-2xl border bg-[#0d0d0d] backdrop-blur-xl
                transition-colors duration-200 group cursor-pointer
                ${isSelected ? 'border-amber-400 ring-2 ring-amber-400/40' : 'border-white/8 hover:border-white/20'}
                ${isTargeted ? 'border-indigo-500 ring-2 ring-indigo-500/40 shadow-[0_0_30px_rgba(99,102,241,0.4)]' : ''}
                ${!isTargeted && !isSelected ? 'hover:shadow-[0_8px_30px_rgba(0,0,0,0.5)]' : ''}
            `}
        >
            {/* ── Top Status Bar (4px) ── */}
            <div className={`h-1 w-full ${cfg.bar} opacity-90`} />

            {/* ── Merge Overlays ── */}
            {isTargeted && (
                <div className="absolute inset-0 bg-indigo-500/10 z-20 flex items-center justify-center backdrop-blur-[2px]">
                    <div className="bg-indigo-600 text-white px-4 py-2 rounded-full font-black shadow-2xl flex items-center gap-2">
                        <GitMerge size={18} className="animate-spin" /> Merge Here
                    </div>
                </div>
            )}
            {isSelected && (
                <div className="absolute inset-0 bg-amber-500/10 z-20 flex items-center justify-center backdrop-blur-[1px]">
                    <div className="bg-amber-500 text-white px-3 py-1 rounded-full font-bold shadow-lg flex items-center gap-2">
                        <GitMerge size={16} /> Source
                    </div>
                </div>
            )}

            {/* ── Card Body ── */}
            <div className="p-5">
                {/* Status Badge + Menu */}
                <div className="flex items-center justify-between mb-3">
                    <span className={`text-[10px] font-black tracking-widest uppercase flex items-center gap-1.5 ${cfg.color}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} animate-pulse`} />
                        {cfg.label}
                    </span>

                    {/* Context menu */}
                    {!isSelectionMode && (
                        <div className="relative" onClick={(e) => e.stopPropagation()}>
                            <button
                                onClick={() => setShowMenu(!showMenu)}
                                className="p-1 opacity-0 group-hover:opacity-100 text-slate-500 hover:text-white transition-all rounded-full hover:bg-white/10"
                            >
                                <MoreHorizontal size={14} />
                            </button>
                            <AnimatePresence>
                                {showMenu && (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.9, y: -5 }}
                                        animate={{ opacity: 1, scale: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                        className="absolute right-0 mt-1 w-36 bg-[#1a1a1a] rounded-xl shadow-2xl border border-white/10 py-1 z-30"
                                    >
                                        <button onClick={() => { setIsEditing(true); setShowMenu(false); }}
                                            className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-white/5 flex items-center gap-2">
                                            <Edit2 size={12} /> Rename
                                        </button>
                                        <button onClick={() => { onDelete(project.id); setShowMenu(false); }}
                                            className="w-full text-left px-3 py-2 text-xs text-red-400 hover:bg-red-500/10 flex items-center gap-2">
                                            <Trash2 size={12} /> Delete
                                        </button>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}
                </div>

                {/* Project Name */}
                {isEditing ? (
                    <div className="flex items-center gap-2 mb-3" onClick={(e) => e.stopPropagation()}>
                        <input
                            ref={inputRef}
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="flex-1 text-lg font-bold text-white bg-white/5 border-b-2 border-cyan-500 outline-none px-1 py-1 rounded-sm"
                        />
                        <button onClick={(e) => { e.stopPropagation(); handleRename(); }}
                            className="p-1.5 bg-cyan-600 text-white rounded-lg">
                            <CheckCircle size={16} />
                        </button>
                    </div>
                ) : (
                    <h3 className="text-lg font-bold tracking-tight text-white mb-1 leading-snug group-hover:text-cyan-200 transition-colors line-clamp-2">
                        {project.meta?.emoji && <span className="mr-2">{project.meta.emoji}</span>}
                        {project.name}
                    </h3>
                )}

                {/* AI Teaser */}
                <p className="text-xs text-slate-500 leading-relaxed mb-4 line-clamp-2 min-h-[2rem]">
                    {teaser}
                </p>

                {/* ── Metrics Row ── */}
                <div className="flex items-center gap-3 text-[11px] text-slate-500 font-medium mb-4">
                    <span className="flex items-center gap-1">
                        <Calendar size={10} />
                        {getLastActive(project)}
                    </span>
                    <span className="flex items-center gap-1">
                        <Zap size={10} className="text-amber-400" />
                        {getVibeLabel(progress, status)}
                    </span>
                </div>

                {/* ── Progress Bar (thick, Nomads-style) ── */}
                <div className="space-y-1.5">
                    <div className="flex justify-between items-center">
                        <span className="text-[10px] text-slate-600 uppercase tracking-wider font-bold">Progress</span>
                        <span className={`text-sm font-black tabular-nums ${cfg.color}`}>{progress}%</span>
                    </div>
                    <div className="h-2.5 w-full bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                            className={`h-full rounded-full ${cfg.bar}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 1, ease: 'easeOut' }}
                            style={{ boxShadow: `0 0 8px var(--tw-shadow-color, #06b6d4)` }}
                        />
                    </div>
                </div>

                {/* ── Click CTA ── */}
                <div className="mt-4 flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className={`text-[10px] font-bold tracking-wider flex items-center gap-1 ${cfg.color}`}>
                        詳情 <ArrowRight size={10} />
                    </span>
                </div>
            </div>

            {showMenu && <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />}
        </motion.div>
    );
};
