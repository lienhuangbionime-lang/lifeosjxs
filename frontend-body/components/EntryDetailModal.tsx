'use client';

import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Save, Trash2, Calendar, Activity, Zap, X, Target } from 'lucide-react';
import { LogEntry } from '@/lib/ai/core';

interface EntryDetailModalProps {
    entry: LogEntry | null;
    isOpen: boolean;
    onClose: () => void;
    onSave: (updatedEntry: LogEntry) => void;
    onDelete: (entryId: string) => void;
}

export const EntryDetailModal = ({ entry, isOpen, onClose, onSave, onDelete }: EntryDetailModalProps) => {
    const [isEditing, setIsEditing] = useState(false);
    const [content, setContent] = useState('');

    // Reset state when entry changes
    useEffect(() => {
        if (entry) {
            // @ts-ignore
            setContent(entry.note || entry.content || '');
            setIsEditing(false);
        }
    }, [entry]);

    const handleSave = () => {
        if (!entry) return;

        // @ts-ignore
        const updated = {
            ...entry,
            note: content,
            content: content // Keep both for backward compat
        };

        onSave(updated);
        setIsEditing(false);
    };

    if (!entry) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={entry.date}
            className="max-w-xl h-[80vh] flex flex-col"
        >
            {/* Header Metrics */}
            <div className="flex items-center justify-between px-6 py-3 bg-slate-50 border-b border-slate-100">
                <div className="flex gap-4 text-xs font-mono text-slate-500">
                    {/* @ts-ignore */}
                    <span className="flex items-center gap-1"><Activity size={12} className="text-blue-500" /> MOOD: {entry.metrics?.mood || entry.mood || '-'}</span>
                    {/* @ts-ignore */}
                    <span className="flex items-center gap-1"><Zap size={12} className="text-yellow-500" /> ENERGY: {entry.metrics?.energy || entry.energy || '-'}</span>
                    {/* @ts-ignore */}
                    <span className="flex items-center gap-1"><Target size={12} className="text-purple-500" /> FOCUS: {entry.metrics?.focus || entry.focus || '-'}</span>
                </div>
                <div className="flex gap-2">
                    {!isEditing ? (
                        <button
                            onClick={() => setIsEditing(true)}
                            className="text-xs font-bold text-indigo-600 hover:text-indigo-700 px-3 py-1 bg-indigo-50 rounded-full transition-colors"
                        >
                            EDIT
                        </button>
                    ) : (
                        <button
                            onClick={() => setIsEditing(false)}
                            className="text-xs font-bold text-slate-500 hover:text-slate-700 px-3 py-1 bg-slate-100 rounded-full transition-colors"
                        >
                            CANCEL
                        </button>
                    )}
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white">
                {isEditing ? (
                    <textarea
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        className="w-full h-full min-h-[300px] text-slate-800 text-sm leading-relaxed outline-none resize-none font-mono"
                        placeholder="Edit log content..."
                        autoFocus
                    />
                ) : (
                    <div className="prose prose-sm max-w-none text-slate-700 font-mono whitespace-pre-wrap leading-relaxed">
                        {content}
                    </div>
                )}
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-between items-center">
                <button
                    onClick={() => {
                        if (window.confirm('Are you sure you want to delete this entry?')) {
                            onDelete(entry.date); // Using date as ID based on current schema usage in frontend
                            onClose();
                        }
                    }}
                    className="flex items-center gap-2 px-4 py-2 text-red-500 hover:bg-red-50 rounded-xl transition-colors text-xs font-bold"
                >
                    <Trash2 size={16} /> DELETE
                </button>

                {isEditing && (
                    <button
                        onClick={handleSave}
                        className="flex items-center gap-2 px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg hover:shadow-indigo-500/20 transition-all text-xs font-bold active:scale-95"
                    >
                        <Save size={16} /> SAVE CHANGES
                    </button>
                )}
            </div>
        </Modal>
    );
};
