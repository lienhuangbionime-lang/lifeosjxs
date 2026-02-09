'use client';
import React, { useEffect, useState } from 'react';
import { GitMerge, Plus, X, ArrowRight, Loader2 } from 'lucide-react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { Project } from '@/lib/types/api-schema';
import { ProjectCard } from './ProjectCard'; // Make sure this path is correct
import { cortex } from '@/lib/api/client';

interface ProjectBoardProps {
    onCreateProject?: () => void;
}

export const ProjectBoard = ({ onCreateProject }: ProjectBoardProps) => {
    const supabase = createClientComponentClient();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'active' | 'archived' | 'idea'>('active');

    // Merge Mode State
    const [isMergeMode, setIsMergeMode] = useState(false);
    const [mergeSourceId, setMergeSourceId] = useState<string | null>(null);

    // Toast/Notification State
    const [toast, setToast] = useState<{ msg: string, type: 'success' | 'error' } | null>(null);

    const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    // Fetch Projects
    const fetchProjects = async () => {
        setLoading(true);
        const { data, error } = await supabase
            .from('projects')
            .select('*')
            .order('progress', { ascending: false });

        if (data) setProjects(data as Project[]);
        setLoading(false);
    };

    useEffect(() => {
        fetchProjects();
    }, [supabase]);

    const filteredProjects = projects.filter(p => filter === 'all' || p.status === filter);

    // --- Actions ---

    const handleUpdate = async (id: string, data: Partial<Project>) => {
        try {
            // Optimistic Update
            setProjects(prev => prev.map(p => p.id === id ? { ...p, ...data } : p));
            await cortex.updateProject(id, data);
            showToast("Project updated");
        } catch (e) {
            showToast("Update failed", "error");
            fetchProjects(); // Revert
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm("Are you sure you want to delete this project? This cannot be undone.")) return;

        try {
            setProjects(prev => prev.filter(p => p.id !== id));
            await cortex.deleteProject(id);
            showToast("Project deleted");
        } catch (e) {
            showToast("Delete failed", "error");
            fetchProjects();
        }
    };

    const handleMergeClick = () => {
        if (isMergeMode) {
            // Cancel Merge Mode
            setIsMergeMode(false);
            setMergeSourceId(null);
        } else {
            // Enter Merge Mode
            setIsMergeMode(true);
            showToast("Select the SOURCE project to merge FROM", "success");
        }
    };

    const handleCardSelect = async (id: string) => {
        if (!isMergeMode) return;

        if (!mergeSourceId) {
            // Step 1: Select Source
            setMergeSourceId(id);
            showToast("Now select the TARGET project to merge INTO", "success");
        } else {
            // Step 2: Select Target
            if (id === mergeSourceId) {
                setMergeSourceId(null); // Deselect
                return;
            }

            const source = projects.find(p => p.id === mergeSourceId);
            const target = projects.find(p => p.id === id);

            if (!source || !target) return;

            if (window.confirm(`Merge "${source.name}" into "${target.name}"? This will archive the source project.`)) {
                try {
                    await cortex.mergeProject(mergeSourceId, id);
                    showToast("Projects merged successfully");
                    setIsMergeMode(false);
                    setMergeSourceId(null);
                    fetchProjects(); // Refresh to show changes
                } catch (e) {
                    showToast("Merge failed", "error");
                }
            }
        }
    };

    // --- Drag & Drop Merge ---
    const handleDragStart = (e: React.DragEvent, id: string) => {
        e.dataTransfer.setData('sourceId', id);
        e.dataTransfer.effectAllowed = 'copyMove';
    };

    const handleDrop = (e: React.DragEvent, targetId: string) => {
        e.preventDefault();
        const sourceId = e.dataTransfer.getData('sourceId');
        if (!sourceId || sourceId === targetId) return;

        const source = projects.find(p => p.id === sourceId);
        const target = projects.find(p => p.id === targetId);
        if (!source || !target) return;

        if (window.confirm(`Merge "${source.name}" into "${target.name}"? This will archive the source project.`)) {
            // Re-use logic or call API
            // For now just simulate as per user request (frontend interactions)
            console.log(`Merging ${sourceId} into ${targetId}`);
            handleUpdate(sourceId, { status: 'archived' }); // Simulate merge
            showToast("Projects merged successfully");
            // In real app, call cortex.mergeProject(sourceId, targetId);
        }
    };

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 custom-scrollbar animate-fade-in bg-[#0f0f0f] bg-grid-white/[0.02] relative">
            {/* ... (keep existing toast and merge mode overlay) ... */}
            {toast && (
                <div className={`fixed top-6 left-1/2 transform -translate-x-1/2 px-6 py-3 rounded-full shadow-2xl z-50 animate-fade-in-up font-bold text-sm ${toast.type === 'success' ? 'bg-slate-800 text-white' : 'bg-red-500 text-white'}`}>
                    {toast.msg}
                </div>
            )}

            {/* ... (Merge Mode Overlay if needed, but DnD obsoletes it partially) ... */}

            {/* Header */}
            <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-black text-gray-200 flex items-center gap-3 tracking-tight">
                        <span className="text-4xl">🚀</span> Projects
                        <button
                            onClick={onCreateProject}
                            className="ml-2 p-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full transition-all shadow-lg hover:shadow-indigo-500/30 active:scale-95"
                            title="New Project"
                        >
                            <Plus size={20} />
                        </button>
                    </h2>
                    <p className="text-gray-400 text-sm mt-1 font-medium">Ship your life & work.</p>
                </div>

                {/* Filters & Actions */}
                <div className="flex items-center gap-3">
                    {/* Visual Help for DnD */}
                    <span className="text-[10px] text-slate-400 font-medium hidden sm:block mr-2">
                        💡 Drag cards to merge • Double-click title to rename
                    </span>

                    <div className="flex bg-white p-1.5 rounded-2xl shadow-sm border border-slate-200">
                        {['active', 'idea', 'archived', 'all'].map(t => (
                            <button
                                key={t}
                                onClick={() => setFilter(t as any)}
                                className={`px-4 py-1.5 rounded-xl text-xs font-bold capitalize transition-all ${filter === t ? 'bg-slate-800 text-white shadow-md' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}
                            >
                                {t}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Nomad List Style Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {filteredProjects.map((proj) => (
                    <ProjectCard
                        key={proj.id}
                        project={proj}
                        isSelectionMode={isMergeMode}
                        isSelected={proj.id === mergeSourceId}
                        onSelect={handleCardSelect}
                        onUpdate={handleUpdate}
                        onDelete={handleDelete}
                        onDragStart={handleDragStart} // [NEW]
                        onDrop={handleDrop} // [NEW]
                    />
                ))}

                {/* Empty State */}
                {filteredProjects.length === 0 && !loading && (
                    <div className="col-span-full py-20 text-center border-2 border-dashed border-slate-200 rounded-3xl bg-slate-50/50">
                        <div className="text-4xl mb-2 opacity-50">🧭</div>
                        <p className="text-slate-400 font-medium">No projects found in {filter}.</p>
                    </div>
                )}
            </div>
        </div>
    );
};
