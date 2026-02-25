'use client';
import React from 'react';
import { AlertCircle, Network, MapPin, Loader2, Trash2, Sparkles, Hash, Calendar, Link as LinkIcon, FolderOpen } from 'lucide-react';
import { CoreEngine } from '@/lib/ai/core';
import { Modal } from '@/components/ui/Modal';
import { cortex } from '@/lib/api/client';
import { Project } from '@/lib/types/api-schema';

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

export const ContextModal = ({ mainNode, logs, onClose, onOpenEntry, onOpenProject }: { mainNode: any, logs: any[], onClose: () => void, onOpenEntry?: (entry: any) => void, onOpenProject?: (project: Project) => void }) => {
    const [dynamicLogs, setDynamicLogs] = React.useState<any[]>([]);
    const [insight, setInsight] = React.useState<string>('');
    const [isLoading, setIsLoading] = React.useState(false);
    const [isInsightLoading, setIsInsightLoading] = React.useState(false);
    const [isDeleting, setIsDeleting] = React.useState(false);
    const [matchingProject, setMatchingProject] = React.useState<Project | null>(null);

    React.useEffect(() => {
        if (!mainNode) {
            setDynamicLogs([]);
            setInsight('');
            return;
        }

        const label = mainNode.label || mainNode.id;

        const checkMatchingProject = async () => {
            try {
                const projects = await cortex.projects.list();
                const match = projects.find(p => p.name === label);
                if (match) setMatchingProject(match);
                else setMatchingProject(null);
            } catch (e) {
                console.warn("Could not check projects for context modal");
            }
        };

        const fetchContext = async () => {
            setIsLoading(true);
            try {
                const results = await cortex.brain.getNodeContext(label);
                const mapped = results.map(r => ({
                    ...r,
                    note: r.content || r.ai_insights || '',
                    matchReason: r.matchReason || { type: 'semantic', label: 'Semantic Match' }
                }));
                setDynamicLogs(mapped);
            } catch (e) {
                console.error("Failed to fetch node context", e);
                setDynamicLogs([]);
            } finally {
                setIsLoading(false);
            }
        };

        const fetchInsight = async () => {
            setIsInsightLoading(true);
            try {
                const res = await cortex.brain.getNodeInsight(label);
                setInsight(res.insight);
            } catch (e) {
                console.error("Failed to fetch node insight", e);
                setInsight('');
            } finally {
                setIsInsightLoading(false);
            }
        };

        checkMatchingProject();
        fetchContext();
        fetchInsight();
    }, [mainNode]);

    if (!mainNode) return null;

    const handleDelete = async () => {
        const nodeLabel = mainNode.label || mainNode.id;
        if (!confirm(`確定要從大腦中刪除「${nodeLabel}」及其所有關聯嗎？`)) return;

        setIsDeleting(true);
        try {
            await cortex.deleteNode(nodeLabel);
            alert('節點已從大腦中移除。');
            onClose();
            window.location.reload();
        } catch (e) {
            console.error(e);
            alert('刪除失敗，請檢查權限或後端連線。');
        } finally {
            setIsDeleting(false);
        }
    };

    const displayLogs = dynamicLogs;

    return (
        <Modal
            isOpen={!!mainNode}
            onClose={onClose}
            className="max-w-xl bg-slate-100"
            title={mainNode.label || mainNode.id}
        >
            <div className="flex-1 flex flex-col max-h-[75vh]">
                <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-white shadow-sm">
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400 uppercase font-mono font-bold tracking-wider">
                            {isLoading ? 'Scanning Synapses...' : `Neural Context (${displayLogs.length})`}
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        {matchingProject && onOpenProject && (
                            <button
                                onClick={() => { onOpenProject(matchingProject); onClose(); }}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50/50 hover:bg-indigo-100 text-indigo-600 rounded-lg text-xs font-bold transition-all shadow-sm border border-indigo-100 hover:shadow-indigo-500/10"
                            >
                                <FolderOpen size={14} /> Open Project
                            </button>
                        )}
                        <button
                            onClick={handleDelete}
                            disabled={isDeleting}
                            className="p-1.5 hover:bg-red-50 rounded-lg text-slate-300 hover:text-red-500 transition-colors"
                            title="Delete from Brain"
                        >
                            {isDeleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                    {/* AI Insight Section */}
                    {(isInsightLoading || insight) && (
                        <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-[1px] rounded-2xl shadow-lg shadow-indigo-200/50">
                            <div className="bg-white/95 backdrop-blur-sm p-4 rounded-[15px]">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="p-1 bg-indigo-100 rounded-lg text-indigo-600">
                                        <Sparkles size={14} />
                                    </div>
                                    <span className="text-xs font-bold text-indigo-600 tracking-wide uppercase">Brain Insight</span>
                                </div>
                                {isInsightLoading ? (
                                    <div className="flex items-center gap-3 py-2">
                                        <Loader2 size={14} className="animate-spin text-indigo-500" />
                                        <div className="h-4 w-full bg-slate-100 rounded animate-pulse" />
                                    </div>
                                ) : (
                                    <p className="text-sm text-slate-700 leading-relaxed italic font-medium">
                                        「{insight}」
                                    </p>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="space-y-3">
                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
                                <Loader2 className="animate-spin text-indigo-500" size={32} />
                                <p className="text-sm italic font-mono animate-pulse">Relinking memories...</p>
                            </div>
                        ) : displayLogs.length > 0 ? (
                            displayLogs.map((log: any, i) => (
                                <div
                                    key={i}
                                    onClick={() => onOpenEntry && onOpenEntry(log)}
                                    className="bg-white p-4 rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-lg transition-all group cursor-pointer active:scale-[0.98]"
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-xs font-mono text-slate-400 bg-slate-50 px-2 py-0.5 rounded-lg border border-slate-100">{log.date}</span>

                                        <span className={`text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1 font-bold border ${log.matchReason?.type === 'semantic' ? 'bg-amber-50 text-amber-600 border-amber-100' :
                                            log.matchReason?.type === 'tag' ? 'bg-pink-50 text-pink-600 border-pink-100' :
                                                log.matchReason?.type === 'date' ? 'bg-indigo-50 text-indigo-600 border-indigo-100' :
                                                    'bg-blue-50 text-blue-600 border-blue-100'
                                            }`}>
                                            {log.matchReason?.type === 'semantic' && <Sparkles size={10} />}
                                            {log.matchReason?.type === 'tag' && <Hash size={10} />}
                                            {log.matchReason?.type === 'date' && <Calendar size={10} />}
                                            {log.matchReason?.type === 'link' && <LinkIcon size={10} />}
                                            {log.matchReason?.label || 'Linked'}
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed">
                                        {((log.note || log.content) || '').replace(/[#*\[\]`>]/g, '')}
                                    </p>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-10 text-slate-400 italic">
                                此節點目前沒有可用的語意關聯。
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Modal>
    );
};
