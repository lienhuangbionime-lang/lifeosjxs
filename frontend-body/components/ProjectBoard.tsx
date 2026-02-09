'use client';
import React, { useEffect, useState } from 'react';
import { LayoutTemplate, FolderKanban, MoreHorizontal, Edit2, Trash2, CheckCircle2, Search, Filter } from 'lucide-react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { Project } from '@/lib/types/api-schema';

export const ProjectBoard = () => {
    const supabase = createClientComponentClient();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'active' | 'archived' | 'idea'>('active');

    // Fetch Projects
    useEffect(() => {
        const fetchProjects = async () => {
            setLoading(true);
            const { data, error } = await supabase
                .from('projects')
                .select('*')
                .order('progress', { ascending: false });

            if (data) setProjects(data as Project[]);
            setLoading(false);
        };
        fetchProjects();
    }, [supabase]);

    const filteredProjects = projects.filter(p => filter === 'all' || p.status === filter);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
            case 'completed': return 'bg-blue-100 text-blue-700 border-blue-200';
            case 'idea': return 'bg-amber-100 text-amber-700 border-amber-200';
            default: return 'bg-slate-100 text-slate-700 border-slate-200';
        }
    };

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 custom-scrollbar animate-fade-in bg-slate-50/50">
            {/* Header */}
            <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-black text-slate-800 flex items-center gap-3 tracking-tight">
                        <span className="text-4xl">🚀</span> Projects
                    </h2>
                    <p className="text-slate-500 text-sm mt-1 font-medium">Ship your life & work.</p>
                </div>

                {/* Filters */}
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

            {/* Nomad List Style Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {filteredProjects.map((proj) => (
                    <div key={proj.id} className="group relative bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden flex flex-col h-64">

                        {/* Cover Image Area */}
                        <div className="h-24 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 relative">
                            {proj.meta?.cover_image && (
                                <img src={proj.meta.cover_image} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity" />
                            )}
                            <div className="absolute -bottom-6 left-4 bg-white p-2 rounded-2xl shadow-sm border border-slate-100 text-2xl">
                                {proj.meta?.emoji || '📦'}
                            </div>
                            <div className={`absolute top-3 right-3 px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border ${getStatusColor(proj.status)}`}>
                                {proj.status}
                            </div>
                        </div>

                        {/* Content */}
                        <div className="pt-8 px-5 pb-5 flex-1 flex flex-col justify-between">
                            <div>
                                <h3 className="font-bold text-slate-800 text-lg leading-tight mb-1 group-hover:text-indigo-600 transition-colors">
                                    {proj.name}
                                </h3>
                                <div className="flex flex-wrap gap-1 mt-2">
                                    {proj.tags?.map(tag => (
                                        <span key={tag} className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-md font-mono">
                                            #{tag}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* Progress & Meta */}
                            <div className="mt-4">
                                <div className="flex justify-between items-end mb-1">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase">Progress</span>
                                    <span className="text-xs font-black text-slate-800">{proj.progress}%</span>
                                </div>
                                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all duration-1000 ease-out"
                                        style={{ width: `${proj.progress}%` }}
                                    />
                                </div>
                                {proj.meta?.vibe && (
                                    <p className="mt-3 text-[10px] text-slate-400 italic truncate">
                                        "{proj.meta.vibe}"
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* Hover Actions */}
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button className="p-1.5 bg-white/90 backdrop-blur rounded-full text-slate-500 hover:text-indigo-600 shadow-sm border border-slate-200">
                                <MoreHorizontal size={14} />
                            </button>
                        </div>
                    </div>
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
