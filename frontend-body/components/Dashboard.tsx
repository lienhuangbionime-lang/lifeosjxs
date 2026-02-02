// 檔案位置: components/Dashboard.tsx
'use client';

import React, { useState } from 'react';
import { Target, Rocket, FileText, RefreshCw, AlertTriangle, Play } from 'lucide-react';

export const Dashboard = () => {
    const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
    const [analysis, setAnalysis] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const handleAnalyze = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/analyze/monthly', { method: 'POST', body: JSON.stringify({ month }) });
            const data = await res.json();
            if(data.success) {
                setAnalysis(data.data);
            } else {
                alert("分析失敗: " + (data.error || "未知錯誤"));
            }
        } catch(e) { 
            console.error(e); 
            alert("系統錯誤，請檢查 Console"); 
        } finally { 
            setLoading(false); 
        }
    };

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 animate-fade-in custom-scrollbar">
            {/* Control Panel */}
            <div className="bg-white p-5 rounded-3xl border border-slate-200 flex justify-between items-center shadow-sm mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl"><Target size={20}/></div>
                    <div>
                        <h2 className="text-slate-800 font-bold">CCA 戰略室</h2>
                        <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="bg-transparent text-slate-500 text-xs font-mono outline-none"/>
                    </div>
                </div>
                <button onClick={handleAnalyze} disabled={loading} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-lg shadow-indigo-200 disabled:opacity-50">
                    {loading ? <RefreshCw className="animate-spin w-4 h-4"/> : <Play className="w-4 h-4"/>}
                    {loading ? "Thinking..." : "Run Agent"}
                </button>
            </div>

            {/* Report Viewer */}
            {analysis ? (
                <div className="space-y-6">
                    {/* Strategy Card - [Fix] 安全存取 strategy */}
                    <div className="bg-gradient-to-br from-indigo-50 to-white p-6 rounded-3xl border border-indigo-100 shadow-sm">
                        <h3 className="text-sm font-bold text-indigo-900 uppercase tracking-widest mb-4">Next Month Strategy</h3>
                        {analysis.strategy ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="p-4 bg-white rounded-2xl border border-indigo-100">
                                    <span className="text-xs text-indigo-400 block mb-1">Focus Project</span>
                                    <span className="text-slate-800 font-bold text-lg">{analysis.strategy.focus_project || '未定義'}</span>
                                </div>
                                <div className="p-4 bg-white rounded-2xl border border-emerald-100">
                                    <span className="text-xs text-emerald-500 block mb-1">New Habits</span>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                        {(analysis.strategy.new_habits || []).map((h:string, i:number) => (
                                            <span key={i} className="text-xs bg-emerald-50 text-emerald-600 px-3 py-1 rounded-full border border-emerald-100">{h}</span>
                                        ))}
                                        {(!analysis.strategy.new_habits || analysis.strategy.new_habits.length === 0) && <span className="text-slate-400 text-xs">無新習慣建議</span>}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="p-4 bg-amber-50 text-amber-600 rounded-xl text-xs flex items-center gap-2"><AlertTriangle size={14}/> 策略資料解析不完整，請查看下方報告。</div>
                        )}
                    </div>

                    {/* Markdown Report */}
                    <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                        <div className="prose prose-sm max-w-none font-mono leading-relaxed text-slate-600">
                            <pre className="whitespace-pre-wrap font-sans">{analysis.content || "無報告內容"}</pre>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center py-20 text-slate-400 italic">準備就緒，等待戰略指令...</div>
            )}
        </div>
    );
};