'use client';

import React, { useState } from 'react';
import { Target, Rocket, FileText, RefreshCw, AlertTriangle } from 'lucide-react';

export const Dashboard = () => {
    const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
    const [analysis, setAnalysis] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const handleAnalyze = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/analyze/monthly', { method: 'POST', body: JSON.stringify({ month }) });
            const data = await res.json();
            if(data.success) setAnalysis(data.data);
            else alert("分析失敗: " + data.error);
        } catch(e) { console.error(e); } finally { setLoading(false); }
    };

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 animate-fade-in">
            {/* Control Panel - Soft Theme */}
            <div className="bg-white p-5 rounded-3xl border border-slate-200 flex justify-between items-center shadow-sm mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl"><Target size={20}/></div>
                    <div>
                        <h2 className="text-slate-800 font-bold">CCA 戰略室</h2>
                        <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="bg-transparent text-slate-500 text-xs font-mono outline-none"/>
                    </div>
                </div>
                <button onClick={handleAnalyze} disabled={loading} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-lg shadow-indigo-200 disabled:opacity-50">
                    {loading ? <RefreshCw className="animate-spin w-4 h-4"/> : <Rocket className="w-4 h-4"/>}
                    {loading ? "Thinking..." : "Run Agent"}
                </button>
            </div>

            {/* Report Viewer */}
            {analysis ? (
                <div className="space-y-6">
                    {/* Strategy Card - [Fix] 安全讀取 strategy */}
                    {analysis.strategy ? (
                        <div className="bg-gradient-to-br from-indigo-50 to-white p-6 rounded-3xl border border-indigo-100 shadow-sm">
                            <h3 className="text-sm font-bold text-indigo-900 uppercase tracking-widest mb-4">Next Month Strategy</h3>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="p-4 bg-white rounded-2xl border border-indigo-100">
                                    <span className="text-xs text-indigo-400 block mb-1">Focus Project</span>
                                    <span className="text-slate-800 font-bold text-lg">{analysis.strategy?.focus_project || '未定義'}</span>
                                </div>
                                <div className="p-4 bg-white rounded-2xl border border-emerald-100">
                                    <span className="text-xs text-emerald-500 block mb-1">New Habits</span>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                        {(analysis.strategy?.new_habits || []).map((h:string, i:number) => (
                                            <span key={i} className="text-xs bg-emerald-50 text-emerald-600 px-3 py-1 rounded-full border border-emerald-100">{h}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="p-4 bg-amber-50 text-amber-600 rounded-xl text-xs flex items-center gap-2"><AlertTriangle size={14}/> 策略資料結構不完整</div>
                    )}

                    {/* Markdown Report */}
                    <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                        <div className="prose prose-sm max-w-none font-mono leading-relaxed text-slate-600">
                            <pre className="whitespace-pre-wrap font-sans">{analysis.content}</pre>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center py-20 text-slate-400 italic">準備就緒，等待戰略指令...</div>
            )}
        </div>
    );
};