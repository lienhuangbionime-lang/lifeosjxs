'use client';
import React, { useState, useRef, useEffect } from 'react';
import { MoreHorizontal, Trash2, Edit2, GitMerge } from 'lucide-react';
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
        if (project.progress >= 80) return { label: '🔥 Hot', color: 'bg-orange-500/20 text-orange-300 border-orange-500/20' };
        if (project.progress >= 50) return { label: '⚡ Active', color: 'bg-blue-500/20 text-blue-300 border-blue-500/20' };
        if (project.status === 'idea') return { label: '💡 Idea', color: 'bg-purple-500/20 text-purple-300 border-purple-500/20' };
        return { label: '🌱 Growing', color: 'bg-green-500/20 text-green-300 border-green-500/20' };
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
                relative overflow-hidden rounded-xl border bg-gray-900/50 backdrop-blur-md 
                transition-all duration-300 group
                ${isSelectionMode ? 'cursor-pointer' : 'hover:border-white/20'}
                ${isSelected ? 'ring-4 ring-amber-400 border-amber-400 scale-95' : 'border-white/10'}
                ${isTargeted ? 'ring-4 ring-indigo-500 border-indigo-500 shadow-[0_0_30px_rgba(99,102,241,0.6)] scale-[1.02]' : ''}
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

            {/* Cover Image with Gradient Overlay */}
            <div className="h-32 relative shrink-0">
                {project.meta?.cover_image ? (
                    <img src={project.meta.cover_image} className="w-full h-full object-cover" alt="" />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500" />
                )}
                {/* Gradient Overlay for Text Clarity */}
                <div className="absolute inset-0 bg-gradient-to-t from-gray-900 to-transparent" />

                {/* Emoji - Floating on Cover */}
                <div className="absolute bottom-3 left-4 text-4xl z-10 drop-shadow-2xl">
                    {project.meta?.emoji || '📦'}
                </div>
            </div>

            {/* Title & Pills */}
            <div className="p-4 space-y-3">
                {isEditing ? (
                    <input
                        ref={inputRef}
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onBlur={handleRename}
                        onKeyDown={handleKeyDown}
                        className="w-full text-xl font-bold text-white bg-white/5 border-b-2 border-indigo-500 outline-none px-1"
                    />
                ) : (
                    <h3
                        onDoubleClick={() => !isSelectionMode && setIsEditing(true)}
                        className="text-xl font-bold text-white tracking-tight cursor-text hover:text-indigo-300 transition-colors"
                        title="Double click to rename"
                    >
                        {project.name}
                    </h3>
                )}

                {/* Data Pills */}
                <div className="flex gap-2 overflow-x-auto no-scrollbar py-2">
                    {/* Vibe Pill */}
                    <span className={`rounded-full px-3 py-1 text-xs font-medium border whitespace-nowrap ${vibe.color}`}>
                        {vibe.label}
                    </span>

                    {/* Status Pill */}
                    <span className="rounded-full px-3 py-1 text-xs font-medium bg-white/5 border border-white/5 text-gray-300 whitespace-nowrap capitalize">
                        {project.status}
                    </span>

                    {/* Tags */}
                    {project.tags?.slice(0, 2).map(tag => (
                        <span key={tag} className="rounded-full px-3 py-1 text-xs font-medium bg-white/5 border border-white/5 text-gray-300 whitespace-nowrap">
                            #{tag}
                        </span>
                    ))}
                </div>
            </div>

            {/* Fluid Progress Bar */}
            <div className="h-1.5 bg-gray-800 relative overflow-hidden">
                <motion.div
                    layoutId={`progress-${project.id}`}
                    className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${project.progress}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
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
