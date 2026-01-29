'use client';
import React from 'react';
import { Network, X, ArrowRight } from 'lucide-react';

export const ContextModal = ({ mainNode, logs, onClose }: { mainNode: any, logs: any[], onClose: () => void }) => {
    if (!mainNode) return null;

    // 關聯邏輯：找出包含該節點標籤或 ID 的日誌
    const relatedLogs = logs.filter(log => {
        const note = log.note || '';
        if (mainNode.group === 'tag') {
            return note.includes(`#${mainNode.id}`);
        } else if (mainNode.group === 'date') {
            return log.date === mainNode.id;
        }
        return false;
    });

    return (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-6 bg-slate-900/80 backdrop-blur-sm animate-fade-in" onClick={onClose}>
            <div className="w-full max-w-lg max-h-[85vh] bg-[#1e293b] rounded-3xl shadow-2xl flex flex-col border border-slate-700" onClick={e => e.stopPropagation()}>
                
                {/* Header */}
                <div className="p-5 border-b border-slate-700 flex justify-between items-center bg-[#1e293b] rounded-t-3xl">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-500/20 rounded-full text-indigo-400">
                            <Network size={20}/>
                        </div>
                        <div>
                            <h3 className="font-bold text-xl text-white">{mainNode.label}</h3>
                            <span className="text-xs text-slate-400 uppercase font-mono">{mainNode.group || 'Node'} Cluster ({relatedLogs.length})</span>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-full text-slate-400 transition-colors"><X size={20}/></button>
                </div>

                {/* Content - Card Clusters */}
                <div className="flex-1 overflow-y-auto p-5 space-y-3 custom-scrollbar">
                    {relatedLogs.length > 0 ? (
                        relatedLogs.map((log, i) => (
                            <div key={i} className="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 hover:border-indigo-500/50 transition-all group">
                                <div className="flex justify-between mb-2">
                                    <span className="text-xs font-mono text-indigo-400">{log.date}</span>
                                    <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400">Focus: {log.metrics?.focus ?? '-'}</span>
                                </div>
                                <p className="text-sm text-slate-300 line-clamp-3 leading-relaxed">{log.note}</p>
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-10 text-slate-500 italic">
                            此節點是孤島，尚無直接關聯紀錄。
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};