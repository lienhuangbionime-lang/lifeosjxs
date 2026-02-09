'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Command, ArrowRight, CornerDownLeft, Moon, Sun, Plus, Layers, Home } from 'lucide-react';
import { useSettings } from '@/lib/hooks/useSettings';

interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
    onNavigate: (tab: string) => void;
    onCreateProject?: () => void;
    activeTab?: string; // Added for compatibility
    logs?: any[]; // Added for compatibility
}

export const CommandPalette = ({ isOpen, onClose, onNavigate, onCreateProject }: CommandPaletteProps) => {
    const [query, setQuery] = useState('');
    const { toggleTheme, theme } = useSettings();
    const [selectedIndex, setSelectedIndex] = useState(0);

    const commands = [
        { id: 'nav-home', label: 'Go to Home', icon: Home, action: () => onNavigate('dashboard') },
        { id: 'nav-projects', label: 'Go to Projects', icon: Layers, action: () => onNavigate('project') },
        { id: 'create-note', label: 'Create New Note', icon: Plus, action: () => onNavigate('capture') },
        { id: 'create-project', label: 'Create New Project', icon: Plus, action: () => { if (onCreateProject) onCreateProject(); else onNavigate('project'); } }, // [NEW]
        { id: 'toggle-theme', label: `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`, icon: theme === 'dark' ? Sun : Moon, action: () => toggleTheme() },
    ];

    const filteredCommands = commands.filter(cmd =>
        cmd.label.toLowerCase().includes(query.toLowerCase())
    );

    // Keyboard Navigation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!isOpen) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedIndex(prev => (prev + 1) % filteredCommands.length);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                filteredCommands[selectedIndex]?.action();
                onClose();
            } else if (e.key === 'Escape') {
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, filteredCommands, selectedIndex, onClose]);

    // Reset selection on query change
    useEffect(() => {
        setSelectedIndex(0);
    }, [query]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh] px-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200" onClick={onClose}>
            <div
                className="w-full max-w-xl bg-[#0f172a] rounded-xl shadow-2xl border border-slate-700 overflow-hidden flex flex-col animate-in zoom-in-95 duration-200"
                onClick={e => e.stopPropagation()}
            >
                <div className="flex items-center px-4 py-3 border-b border-slate-800 gap-3">
                    <Search className="text-slate-400" size={20} />
                    <input
                        autoFocus
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Type a command or search..."
                        className="flex-1 bg-transparent text-lg text-white placeholder:text-slate-600 outline-none"
                    />
                    <div className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 font-mono border border-slate-700">ESC</div>
                </div>

                <div className="max-h-[300px] overflow-y-auto p-2">
                    {filteredCommands.length > 0 ? (
                        filteredCommands.map((cmd, idx) => (
                            <button
                                key={cmd.id}
                                onClick={() => { cmd.action(); onClose(); }}
                                onMouseEnter={() => setSelectedIndex(idx)}
                                className={`w-full flex items-center justify-between px-3 py-3 rounded-lg transition-colors group ${idx === selectedIndex ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                    }`}
                            >
                                <div className="flex items-center gap-3">
                                    <cmd.icon size={18} className={idx === selectedIndex ? 'text-white' : 'text-slate-500 group-hover:text-white'} />
                                    <span className="font-medium text-sm">{cmd.label}</span>
                                </div>
                                {idx === selectedIndex && <CornerDownLeft size={14} className="opacity-50" />}
                            </button>
                        ))
                    ) : (
                        <div className="p-4 text-center text-slate-500 text-sm">No commands found.</div>
                    )}
                </div>

                <div className="bg-slate-900 px-4 py-2 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-500">
                    <div className="flex gap-2">
                        <span><strong className="text-slate-400">↑↓</strong> to navigate</span>
                        <span><strong className="text-slate-400">↵</strong> to select</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
