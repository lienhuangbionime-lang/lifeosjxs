// 檔案位置: components/ContextModal.tsx
'use client';
import React, { useState } from 'react';
import { Network, X, Link as LinkIcon, Calendar, Hash, Trash2, Loader2 } from 'lucide-react';
import { cortex } from '@/lib/api/client';

export const ContextModal = ({ mainNode, logs, onClose }: { mainNode: any, logs: any[], onClose: () => void }) => {
    const [isDeleting, setIsDeleting] = useState(false);
    if (!mainNode) return null;

    const handleDelete = async () => {
        const nodeLabel = mainNode.id || mainNode.label;
        if (!confirm(`確定要從大腦中刪除「${nodeLabel}」及其所有關聯嗎？`)) return;

        setIsDeleting(true);
        try {
            await cortex.deleteNode(nodeLabel);
            alert('節點已從大腦中移除。');
            onClose();
            // 重新載入以刷新圖譜
            window.location.reload();
        } catch (e) {
            console.error(e);
            alert('刪除失敗，請檢查權限或後端連線。');
        } finally {
            setIsDeleting(false);
        }
    };

    // [Fix] 增強關聯邏輯：大小寫不敏感，並支援 Graph Link
    const relatedLogs = logs.map(log => {
        const note = (log.note || '').toLowerCase();
        const nodeId = (mainNode.id || '').toLowerCase();
        let reason = null;

        // 1. Tag 匹配
        if (mainNode.group === 'tag' && (note.includes(`#${nodeId}`) || (log.graphSeeds?.tags || []).some((t: string) => t.toLowerCase() === nodeId))) {
            reason = { type: 'tag', label: `#${mainNode.id || mainNode.label}` };
        }
        // 2. 日期匹配
        else if (mainNode.group === 'date' && log.date === mainNode.id) {
            reason = { type: 'date', label: 'Same Day' };
        }
        // 3. 直接連結 (Link)
        else if (log.graphSeeds?.links?.includes(mainNode.id)) {
            reason = { type: 'link', label: 'Linked' };
        }

        return reason ? { ...log, matchReason: reason } : null;
    }).filter(Boolean);

    return (
        <div className="fixed inset-0 z-[150] flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-sm animate-fade-in" onClick={onClose}>
            <div className="w-full max-w-lg max-h-[85vh] bg-white rounded-3xl shadow-2xl flex flex-col border border-slate-200" onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-3xl">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-100 rounded-full text-indigo-600"><Network size={20} /></div>
                        <div>
                            <h3 className="font-bold text-xl text-slate-800">{mainNode.id || mainNode.label}</h3>
                            <span className="text-xs text-slate-400 uppercase font-mono">Cluster ({relatedLogs.length})</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleDelete}
                            disabled={isDeleting}
                            className="p-2 hover:bg-red-50 rounded-full text-slate-300 hover:text-red-500 transition-colors"
                            title="從大腦中移除"
                        >
                            {isDeleting ? <Loader2 size={20} className="animate-spin" /> : <Trash2 size={20} />}
                        </button>
                        <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors"><X size={20} /></button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-5 space-y-3 custom-scrollbar">
                    {relatedLogs.length > 0 ? (
                        relatedLogs.map((log: any, i) => (
                            <div key={i} className="bg-white p-4 rounded-xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all group">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-xs font-mono text-slate-400 bg-slate-50 px-2 py-1 rounded">{log.date}</span>

                                    <span className={`text-[10px] px-2 py-1 rounded-full flex items-center gap-1 font-bold ${log.matchReason.type === 'tag' ? 'bg-pink-100 text-pink-600' :
                                        log.matchReason.type === 'date' ? 'bg-indigo-100 text-indigo-600' :
                                            'bg-blue-100 text-blue-600'
                                        }`}>
                                        {log.matchReason.type === 'tag' && <Hash size={10} />}
                                        {log.matchReason.type === 'date' && <Calendar size={10} />}
                                        {log.matchReason.type === 'link' && <LinkIcon size={10} />}
                                        {log.matchReason.label}
                                    </span>
                                </div>
                                <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed">{log.note || log.content}</p>
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-10 text-slate-400 italic">
                            此節點 ({mainNode.id || mainNode.label}) 暫無關聯日記。
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};