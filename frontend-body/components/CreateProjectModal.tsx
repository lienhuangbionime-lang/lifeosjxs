'use client';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FolderPlus, Rocket, Zap, Repeat, Smile } from 'lucide-react';
import { cortex } from '@/lib/api/client';

interface CreateProjectModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreated: () => void;
}

export const CreateProjectModal = ({ isOpen, onClose, onCreated }: CreateProjectModalProps) => {
    const [name, setName] = useState('');
    const [category, setCategory] = useState<'macro' | 'micro' | 'daemon'>('macro');
    const [emoji, setEmoji] = useState('✨');
    const [parentId, setParentId] = useState<string>('');
    const [availableAreas, setAvailableAreas] = useState<{ id: string, name: string }[]>([]);
    const [loading, setLoading] = useState(false);

    React.useEffect(() => {
        if (isOpen) {
            // Fetch potential parent areas
            cortex.projects.list().then(projects => {
                const areas = projects.filter(p => !p.parent_id && p.status === 'active');
                setAvailableAreas(areas);
            }).catch(e => console.error("Failed to fetch areas for modal", e));
        }
    }, [isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;

        setLoading(true);
        try {
            await cortex.projects.create({
                name,
                category,
                status: 'active',
                progress: 0,
                meta: { emoji },
                ...(parentId ? { parent_id: parentId } : {})
            });

            onCreated();
            onClose();
            setName('');
            setEmoji('✨');
            setParentId('');
        } catch (error) {
            console.error("Failed to create project", error);
            alert("Failed to create project");
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-md bg-[#0f172a]/90 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/10 overflow-hidden animate-in zoom-in-95 duration-200 ring-1 ring-white/20">
                <div className="p-6 relative">
                    <button onClick={onClose} className="absolute top-4 right-4 text-slate-500 hover:text-white transition-colors">
                        <X size={20} />
                    </button>

                    <div className="mb-6 flex flex-col items-center">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-3xl shadow-lg shadow-indigo-500/30 mb-4 animate-bounce-slow">
                            {emoji}
                        </div>
                        <h2 className="text-2xl font-black text-white">New Project</h2>
                        <p className="text-slate-400 text-sm">Initialize a new neural pathway.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Project Name</label>
                            <input
                                autoFocus
                                value={name}
                                onChange={e => setName(e.target.value)}
                                placeholder="e.g. Build Quantum Engine"
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-indigo-500/50 outline-none transition-all placeholder:text-slate-600"
                            />
                        </div>

                        {availableAreas.length > 0 && (
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Parent Area (Optional)</label>
                                <select
                                    value={parentId}
                                    onChange={(e) => setParentId(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-indigo-500/50 outline-none transition-all appearance-none cursor-pointer"
                                >
                                    <option value="">-- No Parent (Standalone Area) --</option>
                                    {availableAreas.map(area => (
                                        <option key={area.id} value={area.id}>
                                            {area.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Category</label>
                            <div className="grid grid-cols-3 gap-2">
                                {[
                                    { id: 'macro', label: 'Macro', icon: Rocket, desc: 'Big Goal' },
                                    { id: 'micro', label: 'Micro', icon: Zap, desc: 'Quick Win' },
                                    { id: 'daemon', label: 'Daemon', icon: Repeat, desc: 'Routine' },
                                ].map((cat) => (
                                    <button
                                        key={cat.id}
                                        type="button"
                                        onClick={() => setCategory(cat.id as any)}
                                        className={`flex flex-col items-center gap-1 p-3 rounded-xl border transition-all ${category === cat.id
                                            ? 'bg-indigo-500 border-indigo-400 text-white shadow-lg shadow-indigo-500/20'
                                            : 'bg-white/5 border-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
                                            }`}
                                    >
                                        <cat.icon size={18} />
                                        <span className="text-xs font-bold">{cat.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Vibe (Emoji)</label>
                            <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
                                {['✨', '🚀', '💻', '🎨', '🧠', '💰', '🏠', '✈️', '🔥'].map(e => (
                                    <button
                                        key={e}
                                        type="button"
                                        onClick={() => setEmoji(e)}
                                        className={`p-2 rounded-xl text-xl transition-all ${emoji === e ? 'bg-white/20 scale-110' : 'hover:bg-white/5'}`}
                                    >
                                        {e}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 bg-white text-slate-900 rounded-xl font-bold hover:bg-slate-200 transition-colors shadow-lg active:scale-95 disabled:opacity-50"
                        >
                            {loading ? 'Initializing...' : 'Initialize Project'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};
