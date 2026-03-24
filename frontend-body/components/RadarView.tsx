'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radar, Shield, Zap, Target, CheckCircle, ChevronRight, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import { cortex } from '@/lib/api/client';

export const RadarView = () => {
    const [signals, setSignals] = useState<any>({
        watching: [],
        validating: [],
        building: [],
        shipped: []
    });
    const [isLoading, setIsLoading] = useState(true);
    const [isPromoting, setIsPromoting] = useState<string | null>(null);

    const fetchSignals = async () => {
        try {
            setIsLoading(true);
            const data = await cortex.radar.getSignals();
            if (data) setSignals(data);
        } catch (e) {
            console.error("Radar fetch failed", e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchSignals();
    }, []);

    const promoteSignal = async (label: string, nextStatus: string) => {
        setIsPromoting(label);
        try {
            await cortex.radar.promote({ label, target_status: nextStatus });
            await fetchSignals();
        } catch (e) {
            alert("Promotion failed");
        } finally {
            setIsPromoting(null);
        }
    };

    const COLUMNS = [
        { id: 'watching', label: 'Watching', icon: Radar, color: 'text-rose-400', next: 'validating' },
        { id: 'validating', label: 'Validating', icon: Shield, color: 'text-amber-400', next: 'building' },
        { id: 'building', label: 'Building', icon: Zap, color: 'text-cyan-400', next: 'shipped' },
        { id: 'shipped', label: 'Shipped', icon: CheckCircle, color: 'text-emerald-400', next: null }
    ];

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-500">
                <Loader2 className="animate-spin" size={32} />
                <span className="text-xs font-black tracking-widest uppercase">Initializing Radar Radar...</span>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full w-full animate-fade-in p-2">
            
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-indigo-500/10 rounded-2xl border border-indigo-500/20">
                        <Radar className="text-indigo-400 animate-pulse" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-black text-white tracking-tight">Sovereign Radar</h2>
                        <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Signal-to-Sovereignty Pipeline</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button onClick={fetchSignals} className="p-2 hover:bg-slate-800 rounded-xl transition-all text-slate-400 hover:text-white">
                        <Sparkles size={18} />
                    </button>
                </div>
            </div>

            {/* Pipeline Columns */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 h-full overflow-hidden">
                {COLUMNS.map((col) => (
                    <div key={col.id} className="flex flex-col h-full bg-slate-900/40 rounded-[32px] border border-slate-800/50 p-4">
                        <div className="flex items-center justify-between mb-4 px-2">
                            <div className="flex items-center gap-3">
                                <col.icon className={col.color} size={16} />
                                <span className="text-xs font-black uppercase tracking-tighter text-slate-400">{col.label}</span>
                            </div>
                            <span className="text-[10px] font-black bg-slate-800 text-slate-500 py-1 px-2 rounded-full">
                                {signals[col.id]?.length || 0}
                            </span>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3">
                            <AnimatePresence>
                                {signals[col.id]?.map((node: any) => (
                                    <motion.div
                                        key={node.id}
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                        className="group bg-[#020617] border border-slate-800 hover:border-indigo-500/30 p-4 rounded-2xl transition-all relative overflow-hidden"
                                    >
                                        {/* Activity Pulse for 'Watching' */}
                                        {col.id === 'watching' && (
                                            <div className="absolute top-2 right-2 w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.8)]" />
                                        )}

                                        <h3 className="text-sm font-bold text-slate-100 mb-2">{node.label}</h3>
                                        
                                        <div className="flex items-center justify-between mt-4">
                                            <div className="flex -space-x-1 opacity-40">
                                                <div className="w-4 h-4 rounded-full bg-slate-800 border-2 border-slate-900" />
                                                <div className="w-4 h-4 rounded-full bg-slate-800 border-2 border-slate-900" />
                                            </div>
                                            
                                            {col.next && (
                                                <button
                                                    onClick={() => promoteSignal(node.label, col.next!)}
                                                    disabled={isPromoting === node.label}
                                                    className="p-1.5 bg-slate-800 hover:bg-indigo-600 text-slate-400 hover:text-white rounded-lg transition-all"
                                                >
                                                    {isPromoting === node.label ? <Loader2 className="animate-spin" size={14} /> : <ChevronRight size={14} />}
                                                </button>
                                            )}
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                            
                            {signals[col.id]?.length === 0 && (
                                <div className="flex flex-col items-center justify-center h-32 border-2 border-dashed border-slate-800/30 rounded-2xl text-slate-700">
                                    <AlertCircle size={20} className="mb-2 opacity-20" />
                                    <span className="text-[10px] uppercase font-bold tracking-widest opacity-20">Clear Static</span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
