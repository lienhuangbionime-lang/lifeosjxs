'use client';
import React from 'react';
import { AlertCircle, Network, MapPin } from 'lucide-react';
import { CoreEngine } from '@/lib/ai/core';
import { Modal } from '@/components/ui/Modal';

export const ConfirmModal = ({ isOpen, title, message, onConfirm, onCancel }: any) => {
    return (
        <Modal isOpen={isOpen} onClose={onCancel} className="max-w-xs">
            <div className="p-6 text-center">
                <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-6 h-6 text-red-500" />
                </div>
                <h3 className="text-lg font-bold text-slate-800 mb-2">{title}</h3>
                <p className="text-sm text-slate-500 mb-6 leading-relaxed">{message}</p>
                <div className="flex gap-3">
                    <button onClick={onCancel} className="flex-1 py-3 bg-slate-100 text-slate-600 rounded-2xl font-bold text-sm hover:bg-slate-200 transition-colors">取消</button>
                    <button onClick={onConfirm} className="flex-1 py-3 bg-red-500 text-white rounded-2xl font-bold text-sm hover:bg-red-600 shadow-lg transition-colors">確定</button>
                </div>
            </div>
        </Modal>
    );
};

export const ContextModal = ({ mainNode, logs, onClose, onOpenEntry }: any) => {
    const [copied, setCopied] = React.useState(false);

    const connections = React.useMemo(() => {
        if (!mainNode) return [];

        const mainId = mainNode.id;
        const mainSeeds = CoreEngine.parseNoteSeeds((mainNode.note || '') + (mainNode.graphSeeds?.content || ''));
        // If mainNode is a tag, the tag itself is the key constraint
        const mainTags = mainSeeds.tags.length > 0 ? mainSeeds.tags : (mainNode.group === 'tag' ? [mainId] : []);
        const mainLinks = mainSeeds.links || [];

        let mainLog = logs.find((l: any) => l.date === mainId);

        if (!mainLog) {
            // Stub
            mainLog = { date: mainId, note: '', connectionReason: 'Current Focus' };
        } else {
            mainLog = { ...mainLog, connectionReason: 'Current Focus' };
        }

        const related = logs.filter((l: any) => {
            if (l.date === mainId) return false;
            const logSeeds = CoreEngine.parseNoteSeeds((l.note || '') + (l.graphSeeds?.content || ''));
            const logTags = logSeeds.tags || [];
            const logLinks = logSeeds.links || [];

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

    const handleCopy = () => {
        const text = connections.map((c: any) => `[${c.date}] (${c.connectionReason})\n${c.note || ''}`).join('\n\n---\n\n');
        navigator.clipboard.writeText(text).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <Modal isOpen={!!mainNode} onClose={onClose} className="max-w-2xl max-h-[85vh] h-full flex flex-col bg-slate-900/95 border-slate-700 text-white" title={`Context Cluster: ${mainNode?.id}`}>
            <div className="relative h-full flex flex-col">
                <div className="absolute top-[-3.5rem] right-12 z-20">
                    <button
                        onClick={handleCopy}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-black transition-all ${copied ? 'bg-green-500 text-white' : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 border border-slate-600'}`}
                    >
                        {copied ? 'COPIED!' : 'COPY CONTEXT'}
                    </button>
                </div>

                <div className="overflow-y-auto custom-scrollbar p-4 h-full">
                    {connections.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {connections.map((conn: any, idx: number) => (
                                <div key={conn.date} onClick={() => onOpenEntry(conn)}
                                    className={`rounded-xl p-4 cursor-pointer hover:scale-[1.01] transition-all shadow-lg border-l-4 group relative overflow-hidden ${idx === 0 ? 'bg-indigo-900/40 border-indigo-500' : 'bg-slate-800/80 hover:bg-slate-800 border-slate-600'}`}>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="font-bold text-slate-200 text-sm flex items-center gap-2">{conn.date} {idx === 0 && <MapPin size={12} className="text-indigo-400" />}</span>
                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${idx === 0 ? 'bg-indigo-900 text-indigo-300 border-indigo-700' : 'bg-slate-700 text-slate-400 border-slate-600'}`}>{conn.connectionReason}</span>
                                    </div>
                                    <p className="text-xs text-slate-400 line-clamp-2">{conn.note || 'No content'}</p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-white/50 text-center py-10 italic">No direct connections found.</div>
                    )}
                </div>
            </div>
        </Modal>
    );
};
