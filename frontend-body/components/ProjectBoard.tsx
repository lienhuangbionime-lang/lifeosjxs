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
    const [filter, setFilter] = useState<'all' | 'active' | 'archived' | 'idea' | 'completed'>('active');

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
        if (error) console.error("Fetch projects error:", error);
        setLoading(false);
    };

    useEffect(() => {
        fetchProjects();

        // Realtime Subscription
        const channel = supabase
            .channel('realtime projects')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'projects' }, (payload) => {
                console.log('Realtime change:', payload);
                fetchProjects();
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
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
            const executeMerge = async () => {
                try {
                    // Call the real merge API
                    await cortex.mergeProject(sourceId, targetId);
                    showToast("Projects merged successfully");
                    fetchProjects(); // Refresh UI to show archived/merged state
                } catch (e) {
                    console.error("Merge failed:", e);
                    showToast("Merge failed. Please try again.", "error");
                }
            };
            executeMerge();
        }
    };

    return (
        <div className="w-full min-h-screen p-8 overflow-y-auto custom-scrollbar animate-fade-in bg-[#0f0f0f] bg-grid-white/[0.02] relative">
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
                    <h2 className="text-4xl font-black tracking-tighter flex items-center gap-3">
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
                            LifeOS v3.2
                        </span>
                        <button
                            onClick={onCreateProject}
                            className="ml-2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full transition-all shadow-lg hover:shadow-indigo-500/50 active:scale-95 ring-2 ring-indigo-500/30"
                            title="New Project"
                        >
                            <Plus size={20} />
                        </button>
                    </h2>
                    <p className="text-gray-400 text-sm mt-2 font-medium tracking-wide">
                        Ship your life & work • <span className="text-indigo-400">Cyberpunk Edition</span>
                    </p>
                </div>

                {/* Filters & Actions */}
                <div className="flex items-center gap-3">
                    {/* Visual Help for DnD */}
                    <span className="text-[10px] text-gray-500 font-medium hidden sm:block mr-2 uppercase tracking-wider">
                        Drag to Merge
                    </span>

                    <div className="flex gap-2 bg-black/40 p-1.5 rounded-full border border-white/5 backdrop-blur-md">
                        {['active', 'idea', 'completed', 'archived', 'all'].map(t => (
                            <button
                                key={t}
                                onClick={() => setFilter(t as any)}
                                className={`
                                    px-4 py-1.5 rounded-full text-xs font-bold capitalize transition-all duration-300
                                    ${filter === t
                                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-[0_0_15px_rgba(124,58,237,0.5)] scale-105'
                                        : 'text-gray-400 hover:text-white hover:bg-white/5'}
                                `}
                            >
                                {t}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Nomad List Style Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
