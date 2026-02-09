'use client';
import React, { useState, useRef, useEffect } from 'react';
import { MoreHorizontal, Trash2, Edit2, Check, X, GitMerge } from 'lucide-react';
import { Project } from '@/lib/types/api-schema';

interface ProjectCardProps {
    project: Project;
    isSelectionMode: boolean;
    isSelected: boolean;
    onSelect: (id: string) => void;
    onUpdate: (id: string, data: Partial<Project>) => void;
    onDelete: (id: string) => void;
    onDragStart?: (e: React.DragEvent, id: string) => void; // [NEW]
    onDrop?: (e: React.DragEvent, targetId: string) => void; // [NEW]
}

export const ProjectCard = ({ project, isSelectionMode, isSelected, onSelect, onUpdate, onDelete, onDragStart, onDrop }: ProjectCardProps) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editName, setEditName] = useState(project.name);
    const [showMenu, setShowMenu] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    // --- Local State for Drag Target Visuals ---
    const [isTargeted, setIsTargeted] = useState(false);

    // --- Inline Rename Logic ---
    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select(); // Select all text on focus
        }
    }, [isEditing]);

    const handleRename = () => {
        if (editName.trim() && editName !== project.name) {
            onUpdate(project.id, { name: editName });
        }
        setIsEditing(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleRename();
        if (e.key === 'Escape') {
            setEditName(project.name);
            setIsEditing(false);
        }
    };

    // --- Drag & Drop Target Logic ---
    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        // Don't highlight if dragging self (requires checking sourceId from dataTransfer? 
        // HTML5 DnD dataTransfer is protected in dragEnter usually, but we can check visual cues or just allow self-target logic to be handled in drop)
        setIsTargeted(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsTargeted(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault(); // Necessary to allow dropping
        e.stopPropagation();
        // We could optimize to only set isTargeted here if not already, but DragEnter handles it.
    };

    const handleDropInternal = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsTargeted(false);
        if (onDrop) onDrop(e, project.id);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
            case 'completed': return 'bg-blue-100 text-blue-700 border-blue-200';
            case 'idea': return 'bg-amber-100 text-amber-700 border-amber-200';
            default: return 'bg-slate-100 text-slate-700 border-slate-200';
        }
    };

    return (
        <div
            draggable={!isEditing && !isSelectionMode}
            onDragStart={(e) => onDragStart && onDragStart(e, project.id)}

            // Interaction Handlers
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDropInternal}
            onClick={() => isSelectionMode && onSelect(project.id)}

            className={`
                group relative bg-white rounded-3xl border shadow-sm overflow-hidden flex flex-col h-64
                transition-all duration-300
                ${isSelectionMode ? 'cursor-pointer hover:scale-95' : 'hover:shadow-xl hover:-translate-y-1'}
                ${isSelected ? 'ring-4 ring-amber-400 border-amber-400 transform scale-95' : 'border-slate-200'}
                ${isTargeted ? 'ring-4 ring-indigo-500 border-indigo-500 shadow-[0_0_30px_rgba(99,102,241,0.6)] scale-[1.02] z-10' : ''} 
            `}
        >
            {/* Merge Indicator (Target Mode) */}
            {isTargeted && (
                <div className="absolute inset-0 bg-indigo-500/10 z-20 flex items-center justify-center backdrop-blur-[2px] animate-pulse">
                    <div className="bg-indigo-600 text-white px-4 py-2 rounded-full font-black shadow-2xl flex items-center gap-2 transform scale-110">
                        <GitMerge size={20} className="animate-spin-slow" /> Merge Here
                    </div>
                </div>
            )}

            {/* Merge Indicator (Source Mode - when selected) */}
            {isSelected && (
                <div className="absolute inset-0 bg-amber-500/10 z-20 flex items-center justify-center backdrop-blur-[1px]">
                    <div className="bg-amber-500 text-white px-3 py-1 rounded-full font-bold shadow-lg flex items-center gap-2 animate-bounce">
                        <GitMerge size={16} /> Source
                    </div>
                </div>
            )}

            {/* Cover Image Area */}
            <div className={`h-24 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 relative shrink-0 transition-opacity ${isTargeted ? 'opacity-50' : 'opacity-100'}`}>
                {project.meta?.cover_image && (
                    <img src={project.meta.cover_image} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity" />
                )}
                <div className="absolute -bottom-6 left-4 bg-white p-2 rounded-2xl shadow-sm border border-slate-100 text-2xl z-10">
                    {project.meta?.emoji || '📦'}
                </div>
                <div className={`absolute top-3 right-3 px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border ${getStatusColor(project.status)} bg-white/90 backdrop-blur`}>
                    {project.status}
                </div>
            </div>

            {/* Content */}
            <div className="pt-8 px-5 pb-5 flex-1 flex flex-col justify-between">
                <div>
                    {isEditing ? (
                        <div className="flex items-center gap-2 relative">
                            <input
                                ref={inputRef}
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                onBlur={handleRename}
                                onKeyDown={handleKeyDown}
                                className="w-full text-lg font-bold text-slate-800 border-b-2 border-indigo-500 outline-none bg-indigo-50/50 px-1 rounded-t"
                            />
                            <div className="absolute right-0 top-0 text-xs text-slate-400 font-mono">⏎ to save</div>
                        </div>
                    ) : (
                        <h3
                            onDoubleClick={() => !isSelectionMode && setIsEditing(true)}
                            className="font-bold text-slate-800 text-lg leading-tight mb-1 group-hover:text-indigo-600 transition-colors cursor-text selection:bg-indigo-100"
                            title="Double click to rename"
                        >
                            {project.name}
                        </h3>
                    )}

                    <div className="flex flex-wrap gap-1 mt-2">
                        {project.tags?.map(tag => (
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
                        <span className="text-xs font-black text-slate-800">{project.progress}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all duration-1000 ease-out"
                            style={{ width: `${project.progress}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Hover Actions (Only in regular view) */}
            {!isSelectionMode && !isTargeted && (
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <div className="relative">
                        <button
                            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
                            className="p-1.5 bg-white/90 backdrop-blur rounded-full text-slate-500 hover:text-indigo-600 shadow-sm border border-slate-200"
                        >
                            <MoreHorizontal size={14} />
                        </button>

                        {showMenu && (
                            <div className="absolute right-0 mt-2 w-32 bg-white rounded-xl shadow-xl border border-slate-100 py-1 overflow-hidden z-20 animate-in fade-in zoom-in-95 duration-200">
                                <button
                                    onClick={(e) => { e.stopPropagation(); setIsEditing(true); setShowMenu(false); }}
                                    className="w-full text-left px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 flex items-center gap-2"
                                >
                                    <Edit2 size={12} /> Rename
                                </button>
                                <button
                                    onClick={(e) => { e.stopPropagation(); onDelete(project.id); setShowMenu(false); }}
                                    className="w-full text-left px-4 py-2 text-xs font-bold text-red-500 hover:bg-red-50 flex items-center gap-2"
                                >
                                    <Trash2 size={12} /> Delete
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {showMenu && (
                <div className="fixed inset-0 z-0" onClick={() => setShowMenu(false)} />
            )}
        </div>
    );
};
