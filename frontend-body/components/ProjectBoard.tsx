'use client';
import React, { useState, useMemo } from 'react';
import { LayoutTemplate, ChevronRight, Hash, FolderKanban, MoreHorizontal, Edit2, Trash2, ArrowRightLeft, CheckCircle2 } from 'lucide-react';
import { CoreEngine } from '@/lib/ai/core';

interface Project {
    name: string;
    count: number;
    lastUpdate: string;
    type: 'life' | 'work'; // Inferred or Manual
}

interface ProjectBoardProps {
    logs: any[];
    onUpdateLogs: (newLogs: any[]) => void;
}

export const ProjectBoard = ({ logs, onUpdateLogs }: ProjectBoardProps) => {
    const [filter, setFilter] = useState<'all' | 'life' | 'work'>('all');
    const [editingProject, setEditingProject] = useState<string | null>(null);
    const [newName, setNewName] = useState('');
    const [menuOpen, setMenuOpen] = useState<string | null>(null);

    // 1. Aggregate Projects from Logs
    const projects = useMemo(() => {
        const map = new Map<string, Project>();
        (logs || []).forEach(log => {
            const seeds = CoreEngine.parseGraphSeeds(log.note, log.graphSeeds?.content);
            const tags = seeds.tags; // Use standardized extraction

            tags.forEach(tag => {
                if (!map.has(tag)) {
                    // Simple heuristic for Life vs Work (can be improved with AI or manual setting later)
                    const isLife = ['health', 'reading', 'family', 'life', 'gym', 'sleep'].some(k => tag.toLowerCase().includes(k));
                    map.set(tag, {
                        name: tag,
                        count: 0,
                        lastUpdate: log.date,
                        type: isLife ? 'life' : 'work'
                    });
                }
                const p = map.get(tag)!;
                p.count++;
                if (new Date(log.date) > new Date(p.lastUpdate)) p.lastUpdate = log.date;
            });
        });
        return Array.from(map.values()).sort((a, b) => b.count - a.count);
    }, [logs]);

    const filteredProjects = projects.filter(p => filter === 'all' || p.type === filter);

    // 2. Actions
    const handleRename = (oldName: string) => {
        if (!newName.trim() || newName === oldName) return;

        const updatedLogs = logs.map(log => {
            if (!log.note.includes(`#${oldName}`)) return log;
            // Regex replace to ensure we only replace exact tag match
            const noteUpdates = log.note.replace(new RegExp(`#${oldName}\\b`, 'g'), `#${newName}`);
            // Also update graphSeeds tag list if present
            const seeds = log.graphSeeds || {};
            let tagString = seeds.tags || '';
            if (tagString.includes(oldName)) {
                tagString = tagString.replace(new RegExp(`${oldName}\\b`, 'g'), newName);
            }

            return {
                ...log,
                note: noteUpdates,
                graphSeeds: { ...seeds, tags: tagString }
            };
        });

        onUpdateLogs(updatedLogs);
        setEditingProject(null);
        setMenuOpen(null);
    };

    const handleDelete = (targetName: string) => {
        if (!confirm(`確定要刪除專案 #${targetName} 嗎？\n這將會從所有日誌中移除此標籤。`)) return;

        const updatedLogs = logs.map(log => {
            if (!log.note.includes(`#${targetName}`)) return log;
            const noteUpdates = log.note.replace(new RegExp(`#${targetName}\\b`, 'g'), '');
            return { ...log, note: noteUpdates };
        });

        onUpdateLogs(updatedLogs);
        setMenuOpen(null);
    };

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 custom-scrollbar animate-fade-in">
            <div className="mb-6 flex justify-between items-end">
                <div>
                    <h2 className="text-2xl font-bold text-slate-700 flex items-center gap-2">
                        <LayoutTemplate className="text-indigo-500" /> Project Board
                    </h2>
                    <p className="text-slate-400 text-xs mt-1">Manage your Life & Work projects</p>
                </div>

                {/* Filter Tabs */}
                <div className="flex bg-slate-100 p-1 rounded-xl">
                    {['all', 'work', 'life'].map(t => (
                        <button
                            key={t}
                            onClick={() => setFilter(t as any)}
                            className={`px-3 py-1 rounded-lg text-xs font-bold capitalize transition-all ${filter === t ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredProjects.map((proj) => (
                    <div key={proj.name} className="relative bg-white p-4 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all group">

                        <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-sm ${proj.type === 'life' ? 'bg-emerald-400' : 'bg-indigo-400'}`}>
                                    {proj.name[0].toUpperCase()}
                                </div>
                                <div>
                                    {editingProject === proj.name ? (
                                        <div className="flex items-center gap-2">
                                            <input
                                                autoFocus
                                                value={newName}
                                                onChange={e => setNewName(e.target.value)}
                                                className="bg-slate-50 border border-indigo-300 rounded px-2 py-0.5 text-sm font-bold text-slate-700 outline-none"
                                            />
                                            <button onClick={() => handleRename(proj.name)} className="text-emerald-500 hover:bg-emerald-50 p-1 rounded"><CheckCircle2 size={16} /></button>
                                        </div>
                                    ) : (
                                        <h3 className="font-bold text-slate-700 text-base flex items-center gap-2">
                                            #{proj.name}
                                        </h3>
                                    )}
                                    <span className="text-[10px] text-slate-400 font-mono">Updated: {proj.lastUpdate}</span>
                                </div>
                            </div>

                            <div className="relative">
                                <button onClick={() => setMenuOpen(menuOpen === proj.name ? null : proj.name)} className="p-1 rounded-full hover:bg-slate-100 text-slate-400">
                                    <MoreHorizontal size={16} />
                                </button>

                                {menuOpen === proj.name && (
                                    <div className="absolute right-0 top-8 bg-white border border-slate-200 rounded-xl shadow-xl z-20 w-32 overflow-hidden animate-scale-in">
                                        <button onClick={() => { setEditingProject(proj.name); setNewName(proj.name); setMenuOpen(null); }} className="w-full text-left px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 flex items-center gap-2">
                                            <Edit2 size={12} /> Rename
                                        </button>
                                        <button onClick={() => handleDelete(proj.name)} className="w-full text-left px-4 py-2 text-xs font-bold text-red-500 hover:bg-red-50 flex items-center gap-2">
                                            <Trash2 size={12} /> Delete
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex items-center justify-between mt-3">
                            <span className="text-xs font-bold bg-slate-50 text-slate-500 px-2 py-1 rounded-md border border-slate-100">
                                {proj.count} logs
                            </span>
                            <span className={`text-[10px] uppercase font-black px-2 py-0.5 rounded-full ${proj.type === 'life' ? 'bg-emerald-50 text-emerald-600' : 'bg-indigo-50 text-indigo-600'}`}>
                                {proj.type}
                            </span>
                        </div>
                    </div>
                ))}

                {filteredProjects.length === 0 && (
                    <div className="col-span-full flex flex-col items-center justify-center py-20 text-slate-400 border-2 border-dashed border-slate-200 rounded-3xl bg-slate-50">
                        <FolderKanban size={48} className="mb-4 opacity-20" />
                        <p className="text-sm">No projects found.</p>
                        <p className="text-xs mt-2 opacity-50">Use #Tags in your logs to create projects.</p>
                    </div>
                )}
            </div>
        </div>
    );
};
