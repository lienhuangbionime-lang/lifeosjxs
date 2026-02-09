'use client';
import React from 'react';
import { AlertCircle, Network, MapPin } from 'lucide-react';
import { CoreEngine, NEON_PALETTE } from '@/lib/ai/core';

export const ConfirmModal = ({ isOpen, title, message, onConfirm, onCancel }: any) => {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 z-[150] flex items-center justify-center p-4 animate-fade-in">
            <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-all" onClick={onCancel} />
            <div className="bg-white/95 w-full max-w-xs rounded-3xl shadow-2xl p-6 relative z-10 animate-scale-in text-center border border-white/20 backdrop-blur-md">
                <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4"><AlertCircle className="w-6 h-6 text-red-500" /></div>
                <h3 className="text-lg font-bold text-slate-800 mb-2">{title}</h3>
                <p className="text-sm text-slate-500 mb-6 leading-relaxed">{message}</p>
                <div className="flex gap-3">
                    <button onClick={onCancel} className="flex-1 py-3 bg-slate-100 text-slate-600 rounded-2xl font-bold text-sm hover:bg-slate-200">取消</button>
                    <button onClick={onConfirm} className="flex-1 py-3 bg-red-500 text-white rounded-2xl font-bold text-sm hover:bg-red-600 shadow-lg">確定</button>
                </div>
            </div>
        </div>
    );
};

export const ContextModal = ({ mainNode, logs, onClose, onOpenEntry }: any) => {
    const connections = React.useMemo(() => {
        if (!mainNode) return [];

        const mainId = mainNode.id;
        const mainSeeds = CoreEngine.parseGraphSeeds(mainNode.note, mainNode.graphSeeds?.content);
        // If mainNode is a tag, the tag itself is the key constraint
        const mainTags = mainSeeds.tags.length > 0 ? mainSeeds.tags : (mainNode.group === 'tag' ? [mainId] : []);
        const mainLinks = mainSeeds.links;

        let mainLog = logs.find((l: any) => l.date === mainId);

        if (!mainLog) {
            mainLog = CoreEngine.generateStubLog(mainId, mainNode.group);
            mainLog.connectionReason = 'Current Focus';
        } else {
            mainLog.connectionReason = 'Current Focus';
        }

        const related = logs.filter((l: any) => {
            if (l.date === mainId) return false;
            const logSeeds = CoreEngine.parseGraphSeeds(l.note, l.graphSeeds?.content);
            const logTags = logSeeds.tags;
            const logLinks = logSeeds.links;

            const sharedTags = logTags.filter((t: string) => mainTags.includes(t));
            const isLinked = logLinks.includes(mainId) || mainLinks.includes(l.date);
            const isTaggedWithMain = (mainNode.group === 'tag') && logTags.includes(mainId);

            if (sharedTags.length > 0 || isLinked || isTaggedWithMain) {
                if (isLinked) l.connectionReason = 'Direct Link';
                else if (isTaggedWithMain) l.connectionReason = 'Tagged';
                else l.connectionReason = `#${sharedTags[0]}`;
                return true;
            }
            return false;
        }).slice(0, 10);

        return [mainLog, ...related];
    }, [mainNode, logs]);

    if (!mainNode) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm animate-fade-in" onClick={onClose}>
            <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto custom-scrollbar bg-transparent flex flex-col gap-4 animate-scale-in" onClick={e => e.stopPropagation()}>
                <div className="flex items-center gap-2 text-white/80 pb-2 border-b border-white/10">
                    <Network className="w-5 h-5" />
                    <span className="font-bold text-lg tracking-tight">Context Cluster: {mainNode.id}</span>
                </div>
                {connections.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {connections.map((conn: any, idx: number) => (
                            <div key={conn.date} onClick={() => onOpenEntry(conn)}
                                className={`rounded-xl p-4 cursor-pointer hover:scale-[1.01] transition-all shadow-lg border-l-4 group relative overflow-hidden ${idx === 0 ? 'bg-indigo-50 border-indigo-500 ring-2 ring-indigo-200' : 'bg-white/95 backdrop-blur hover:bg-white border-slate-300'}`}>
                                <div className="flex justify-between items-center mb-1">
                                    <span className="font-bold text-slate-800 text-sm flex items-center gap-2">{conn.date} {idx === 0 && <MapPin size={12} className="text-indigo-600" />}</span>
                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${idx === 0 ? 'bg-indigo-100 text-indigo-700 border-indigo-200' : 'bg-slate-100 text-slate-600 border-slate-200'}`}>{conn.connectionReason}</span>
                                </div>
                                <p className="text-xs text-slate-500 line-clamp-2">{CoreEngine.extractInsight(conn.note).text}</p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-white/50 text-center py-10 italic">No direct connections found.</div>
                )}
            </div>
        </div>
    );
};
