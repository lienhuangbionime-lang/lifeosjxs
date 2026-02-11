'use client';
import React, { useState, useRef, useEffect } from 'react';
import { MoreHorizontal, Trash2, Edit2, GitMerge, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { Project } from '@/lib/types/api-schema';

interface ProjectCardProps {
    project: Project;
    isSelectionMode: boolean;
    isSelected: boolean;
    onSelect: (id: string) => void;
    onUpdate: (id: string, data: Partial<Project>) => void;
    onDelete: (id: string) => void;
    onDragStart?: (e: React.DragEvent, id: string) => void;
    onDrop?: (e: React.DragEvent, targetId: string) => void;
}

export const ProjectCard = ({ project, isSelectionMode, isSelected, onSelect, onUpdate, onDelete, onDragStart, onDrop }: ProjectCardProps) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editName, setEditName] = useState(project.name);
    const [showMenu, setShowMenu] = useState(false);
    const [isTargeted, setIsTargeted] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
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

    // Drag & Drop Handlers
    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsTargeted(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsTargeted(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDropInternal = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsTargeted(false);
        if (onDrop) onDrop(e, project.id);
    };

    // Vibe Pill Logic
    const getVibePill = () => {
        // Mock logic for "High Energy" based on progress, or random tag
        if (project.progress >= 80) return { label: 'HIGH ENERGY', color: 'bg-orange-500/20 text-orange-300 border-orange-500/30' };
        if (project.progress >= 50) return { label: 'ACTIVE FLOW', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' };
        if (project.status === 'idea') return { label: 'CONCEPT', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' };
        return { label: 'CHILL', color: 'bg-green-500/20 text-green-300 border-green-500/30' };
    };

    const vibe = getVibePill();

    return (
        <div
            draggable={!isEditing && !isSelectionMode}
            onDragStart={(e) => onDragStart && onDragStart(e, project.id)}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDropInternal}
            onClick={() => isSelectionMode && onSelect(project.id)}
            className={`
                relative overflow-hidden rounded-2xl border border-white/10 bg-gray-900/60 backdrop-blur-xl 
                transition-all duration-300 group
                ${isSelectionMode ? 'cursor-pointer' : 'hover:border-white/20 hover:shadow-[0_0_20px_rgba(0,255,255,0.1)]'}
                ${isSelected ? 'ring-2 ring-amber-400 border-amber-400 scale-95' : ''}
                ${isTargeted ? 'ring-2 ring-indigo-500 border-indigo-500 shadow-[0_0_30px_rgba(99,102,241,0.6)] scale-[1.02]' : ''}
            `}
        >
            {/* Merge Indicators */}
            {isTargeted && (
                <div className="absolute inset-0 bg-indigo-500/10 z-20 flex items-center justify-center backdrop-blur-[2px] animate-pulse">
                    <div className="bg-indigo-600 text-white px-4 py-2 rounded-full font-black shadow-2xl flex items-center gap-2">
                        <GitMerge size={20} className="animate-spin" /> Merge Here
                    </div>
                </div>
            )}

            {isSelected && (
                <div className="absolute inset-0 bg-amber-500/10 z-20 flex items-center justify-center backdrop-blur-[1px]">
                    <div className="bg-amber-500 text-white px-3 py-1 rounded-full font-bold shadow-lg flex items-center gap-2 animate-bounce">
                        <GitMerge size={16} /> Source
                    </div>
                </div>
            )}

            {/* Header Image (Cover) */}
            <div className="h-32 relative shrink-0">
                {project.meta?.cover_image ? (
                    <img src={project.meta.cover_image} className="w-full h-full object-cover" alt="" />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-gray-800 to-gray-900" />
                )}
                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/40 to-transparent" />

                {/* Emoji - Floating on Cover */}
                <div className="text-4xl absolute bottom-[-16px] left-4 drop-shadow-lg z-10">
                    {project.meta?.emoji || '📦'}
                </div>
            </div>

            {/* Title */}
            <div className="mt-6 px-4">
                {isEditing ? (
                    <div className="flex items-center gap-2">
                        <input
                            ref={inputRef}
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="flex-1 text-xl font-bold text-white bg-white/5 border-b-2 border-indigo-500 outline-none px-1 py-1"
                        />
                        <button
                            onClick={(e) => { e.stopPropagation(); handleRename(); }}
                            className="p-2 bg-indigo-600 text-white rounded-lg shadow-lg"
                        >
                            <CheckCircle size={18} />
                        </button>
                    </div>
                ) : (
                    <div className="flex items-center justify-between group/title">
                        <h3
                            onClick={() => !isSelectionMode && setIsEditing(true)}
                            className="text-xl font-bold tracking-tight text-white cursor-pointer hover:text-indigo-300 transition-colors flex-1"
                            title="Click to rename"
                        >
                            {project.name}
                        </h3>
                        <button
                            onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
                            className="opacity-0 group-hover/title:opacity-100 p-1 text-slate-500 hover:text-indigo-400 transition-all"
                        >
                            <Edit2 size={14} />
                        </button>
                    </div>
                )}
            </div>

            {/* Meta Pills */}
            <div className="px-4 mt-2 flex gap-2 overflow-x-auto no-scrollbar">
                {/* Vibe Pill */}
                <span className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded-md bg-white/5 border border-white/5 whitespace-nowrap ${vibe.color}`}>
                    {vibe.label}
                </span>

                {/* Tags */}
                {project.tags?.slice(0, 2).map(tag => (
                    <span key={tag} className="text-[10px] uppercase tracking-wider px-2 py-1 rounded-md bg-white/5 border border-white/5 text-gray-400 whitespace-nowrap">
                        #{tag}
                    </span>
                ))}
            </div>

            {/* Fluid Progress Bar */}
            <div className="h-1.5 w-full bg-gray-800 mt-4 relative overflow-hidden">
                <motion.div
                    className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${project.progress}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    style={{
                        boxShadow: '0 0 10px #bc13fe'
                    }}
                />
            </div>

            {/* Hover Actions */}
            {!isSelectionMode && !isTargeted && (
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <div className="relative">
                        <button
                            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
                            className="p-1.5 bg-black/60 backdrop-blur rounded-full text-gray-300 hover:text-white shadow-lg border border-white/10"
                        >
                            <MoreHorizontal size={14} />
                        </button>

                        {showMenu && (
                            <div className="absolute right-0 mt-2 w-32 bg-gray-900 rounded-xl shadow-2xl border border-white/10 py-1 overflow-hidden z-20">
                                <button
                                    onClick={(e) => { e.stopPropagation(); setIsEditing(true); setShowMenu(false); }}
                                    className="w-full text-left px-4 py-2 text-xs font-medium text-gray-300 hover:bg-white/5 flex items-center gap-2"
                                >
                                    <Edit2 size={12} /> Rename
                                </button>
                                <button
                                    onClick={(e) => { e.stopPropagation(); onDelete(project.id); setShowMenu(false); }}
                                    className="w-full text-left px-4 py-2 text-xs font-bold text-red-400 hover:bg-red-500/10 flex items-center gap-2"
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
