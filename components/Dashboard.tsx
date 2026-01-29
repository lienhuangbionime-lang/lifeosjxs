'use client';

import React, { useState } from 'react';
import { Target, Rocket, FileText, RefreshCw } from 'lucide-react';

export const Dashboard = () => {
    const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
    const [analysis, setAnalysis] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const handleAnalyze = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/analyze/monthly', {
                method: 'POST',
                body: JSON.stringify({ month })
            });
            const data = await res.json();
            if(data.success) {
                setAnalysis(data.data);
            } else {
                alert("分析失敗: " + data.error);
            }
        } catch(e) {
            console.error(e);
            alert("系統錯誤");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-full pb-24 space-y-6 animate-fade-in">
            {/* Control Panel */}
            <div className="bg-[#1e293b] p-5 rounded-3xl border border-slate-700 flex justify-between items-center shadow-lg">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-indigo-500/20 rounded-full text-indigo-400"><Target size={20}/></div>
                    <div>
                        <h2 className="text-white font-bold">CCA 戰略室</h2>
                        <input 
                            type="month" 
                            value={month} 
                            onChange={(e) => setMonth(e.target.value)} 
                            className="bg-transparent text-slate-400 text-xs font-mono outline-none cursor-pointer hover:text-white"
                        />
                    </div>
                </div>
                <button 
                    onClick={handleAnalyze} 
                    disabled={loading}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-lg shadow-indigo-500/30 disabled:opacity-50"
                >
                    {loading ? <RefreshCw className="animate-spin w-4 h-4"/> : <Rocket className="w-4 h-4"/>}
                    {loading ? "Analyzing..." : "Run Agent"}
                </button>
            </div>

            {/* Report Viewer */}
            {analysis ? (
                <div className="space-y-6">
                    {/* Strategy Card */}
                    {analysis.strategy && (
                        <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-3xl border border-slate-700">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Next Month Strategy</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 bg-slate-800/50 rounded-2xl border border-slate-700/50">
                                    <span className="text-xs text-indigo-400 block mb-1">Focus Project</span>
                                    <span className="text-white font-bold">{analysis.strategy.focus_project || 'N/A'}</span>
                                </div>
                                <div className="p-4 bg-slate-800/50 rounded-2xl border border-slate-700/50">
                                    <span className="text-xs text-emerald-400 block mb-1">New Habits</span>
                                    <div className="flex flex-wrap gap-1">
                                        {(analysis.strategy.new_habits || []).map((h:string) => (
                                            <span key={h} className="text-[10px] bg-emerald-500/10 text-emerald-300 px-2 py-1 rounded">{h}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Markdown Report */}
                    <div className="bg-[#1e293b] p-6 rounded-3xl border border-slate-700 shadow-lg">
                        <div className="prose prose-invert prose-sm max-w-none font-mono leading-relaxed">
                            <pre className="whitespace-pre-wrap font-sans text-slate-300">{analysis.content}</pre>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center py-20 text-slate-600 italic">
                    選擇月份並點擊 Run Agent 以生成復盤報告...
                </div>
            )}
        </div>
    );
};