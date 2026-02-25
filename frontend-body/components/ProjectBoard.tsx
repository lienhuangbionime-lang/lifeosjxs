'use client';
import React, { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { Project } from '@/lib/types/api-schema';
import { ProjectCard } from './ProjectCard';
import { ProjectDetailPanel } from './ProjectDetailPanel';
import { cortex } from '@/lib/api/client';

interface ProjectBoardProps {
    onCreateProject?: () => void;
    incomingProject?: Project | null;
    onJumpToGraph?: (projectName: string) => void;
}

export const ProjectBoard = ({ onCreateProject, incomingProject, onJumpToGraph }: ProjectBoardProps) => {
    const supabase = createClientComponentClient();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'active' | 'archived' | 'idea' | 'completed'>('active');
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);

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

    useEffect(() => {
        if (incomingProject) {
            setSelectedProject(incomingProject);
        }
    }, [incomingProject]);

    const filteredProjects = projects.filter(p => filter === 'all' || p.status === filter);
    const rootProjects = filteredProjects.filter(p => !p.parent_id || !filteredProjects.some(parent => parent.id === p.parent_id));

    // --- Actions ---

    const handleUpdate = async (id: string, data: Partial<Project>) => {
        try {
            // Optimistic Update
            setProjects(prev => prev.map(p => p.id === id ? { ...p, ...data } : p));
            await cortex.projects.update(id, data);
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
            await cortex.projects.delete(id);
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
                    await cortex.projects.merge(mergeSourceId, id);
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
                    await cortex.projects.merge(sourceId, targetId);
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

            {/* Project Detail Panel */}
            <ProjectDetailPanel
                project={selectedProject}
                onClose={() => setSelectedProject(null)}
                onUpdate={handleUpdate}
                onJumpToGraph={onJumpToGraph}
            />

            {/* Hierarchical Grid */}
            <div className="flex flex-col gap-12">
                {rootProjects.map((rootProj) => {
                    const children = filteredProjects.filter(p => p.parent_id === rootProj.id);
                    return (
                        <div key={rootProj.id} className="flex flex-col gap-6 relative">
                            {/* Area / Root Project */}
                            <div className="w-full sm:w-1/2 md:w-1/2 lg:w-1/3 xl:w-1/4">
                                <ProjectCard
                                    project={rootProj}
                                    isSelectionMode={isMergeMode}
                                    isSelected={rootProj.id === mergeSourceId}
                                    onSelect={handleCardSelect}
                                    onUpdate={handleUpdate}
                                    onDelete={handleDelete}
                                    onOpen={(p) => setSelectedProject(p)}
                                    onDragStart={handleDragStart}
                                    onDrop={handleDrop}
                                />
                            </div>

                            {/* Children Projects */}
                            {children.length > 0 && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 ml-4 md:ml-12 pl-4 md:pl-8 border-l-2 border-slate-800/60">
                                    {children.map(child => (
                                        <div key={child.id} className="relative">
                                            {/* Branch connection visual */}
                                            <div className="absolute top-1/2 -left-4 md:-left-8 w-4 md:w-8 h-[2px] bg-slate-800/60 -z-10" />
                                            <ProjectCard
                                                project={child}
                                                isSelectionMode={isMergeMode}
                                                isSelected={child.id === mergeSourceId}
                                                onSelect={handleCardSelect}
                                                onUpdate={handleUpdate}
                                                onDelete={handleDelete}
                                                onOpen={(p) => setSelectedProject(p)}
                                                onDragStart={handleDragStart}
                                                onDrop={handleDrop}
                                            />
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}

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
