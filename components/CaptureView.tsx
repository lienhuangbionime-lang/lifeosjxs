'use client';

import React, { useState, useEffect } from 'react';
import { PenTool, Cpu, Activity, Terminal, CheckCircle, AlertTriangle } from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';

export const CaptureView = ({ onSave }: { onSave: (log: any) => void }) => {
    const [entry, setEntry] = useState<any>({ 
        date: '', note: '', mood: 5, focus: 5, energy: 5, deepWork: 0, habits: {} 
    });
    const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
    const [aiThinkingLogs, setAiThinkingLogs] = useState<string[]>([]);
    const [detectedTasks, setDetectedTasks] = useState<string[]>([]);

    useEffect(() => {
        setEntry((prev: any) => ({ ...prev, date: new Date().toISOString().split('T')[0] }));
    }, []);

    // [Fix] 這是真正的 AI 呼叫邏輯，不再是 setTimeout 模擬
    const handleAIParse = async () => {
        if (!entry.note) return alert("❌ 請輸入內容");
        
        setIsAiAnalyzing(true);
        setAiThinkingLogs(["連線神經網絡...", "正在讀取脈絡..."]);
        
        try {
            // 1. 呼叫後端 API (這裡是你設定的 Gemini 1.5 Flash)
            const response = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: entry.note, 
                    date: entry.date 
                })
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || "API 回應錯誤");
            }

            // 2. 成功獲取 AI 思考結果
            setAiThinkingLogs(prev => [...prev, "✅ 分析完成", `Model: ${result.model || 'Gemini'}`]);
            
            // 3. 解析回傳資料 (更新介面)
            // 後端回傳的 data 結構: { meta: { metrics... }, markdown_body: "...", tasks: [] }
            const aiData = result.data || {}; // 防呆
            const metrics = aiData.meta?.metrics || {};

            // 4. 更新前端狀態
            setEntry((prev: any) => ({
                ...prev,
                note: result.data.markdown_body, // 填入整理好的 Markdown (含簽名檔)
                mood: metrics.mood ?? prev.mood,
                focus: metrics.focus ?? prev.focus,
                energy: metrics.energy ?? prev.energy,
                // 如果後端有回傳 habits，也可以在這裡更新
            }));

            // 5. 更新任務清單
            if (aiData.tasks && Array.isArray(aiData.tasks)) {
                setDetectedTasks(aiData.tasks.map((t: any) => t.title));
                setAiThinkingLogs(prev => [...prev, `⚡ 提取了 ${aiData.tasks.length} 個行動`]);
            }

        } catch (e: any) {
            console.error("AI Error:", e);
            setAiThinkingLogs(prev => [...prev, `❌ 錯誤: ${e.message}`]);
            alert("AI 連線失敗，請檢查 API Key 或 Vercel Logs");
        } finally {
            setIsAiAnalyzing(false);
        }
    };

    const handleSave = () => {
        const seeds = CoreEngine ? CoreEngine.parseGraphSeeds(entry.note) : { tags: [], links: [] };
        onSave({ ...entry, graphSeeds: seeds });
        // 重置
        setEntry({ date: new Date().toISOString().split('T')[0], note: '', mood: 5, focus: 5, energy: 5, deepWork: 0, habits: {} });
        setDetectedTasks([]);
        setAiThinkingLogs([]);
    };

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 custom-scrollbar">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                   <PenTool className="text-indigo-500" /> Capture Flow
                </h2>
                <p className="text-slate-400 text-xs mt-1">紀錄當下，讓 AI 幫你整理結構</p>
            </div>
            
            {/* AI Terminal */}
            {(isAiAnalyzing || aiThinkingLogs.length > 0) && (
                <div className="mb-6 bg-slate-900 rounded-2xl p-4 shadow-xl border border-slate-800">
                    <div className="flex items-center gap-2 mb-2 border-b border-slate-800 pb-2">
                        <Terminal size={14} className="text-emerald-400 animate-pulse"/>
                        <span className="text-xs font-mono text-emerald-400 font-bold">AI_CORE_PROCESSOR</span>
                    </div>
                    <div className="font-mono text-xs space-y-1 h-32 overflow-y-auto custom-scrollbar flex flex-col-reverse">
                        {isAiAnalyzing && <div className="text-emerald-500 animate-pulse">_</div>}
                        {[...aiThinkingLogs].reverse().map((log, i) => (
                            <div key={i} className="text-slate-300"><span className="text-indigo-500 mr-2">➜</span>{log}</div>
                        ))}
                    </div>
                </div>
            )}

            {/* Input Card */}
            <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-200">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Daily Log</span>
                    <input type="date" value={entry.date} onChange={e => setEntry({...entry, date: e.target.value})} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1 text-sm font-mono text-slate-600 outline-none"/>
                </div>
                <textarea 
                    value={entry.note} onChange={e => setEntry({...entry, note: e.target.value})}
                    placeholder="# 輸入想法...\n> Agent 會幫你整理成 Project 與 Life 雙軌"
                    className="w-full h-48 p-4 bg-slate-50 border border-slate-100 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-100 outline-none resize-none leading-relaxed text-slate-700 placeholder:text-slate-400"
                />
                
                {detectedTasks.length > 0 && (
                    <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
                        <div className="text-xs font-bold text-indigo-500 mb-2 flex items-center gap-2"><CheckCircle size={12}/> Extracted Tasks</div>
                        <ul className="space-y-1">
                            {detectedTasks.map((t, i) => <li key={i} className="text-xs text-indigo-700 flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>{t}</li>)}
                        </ul>
                    </div>
                )}

                <div className="flex justify-end gap-2 mt-4">
                    <button onClick={handleAIParse} disabled={isAiAnalyzing} className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 transition-colors flex items-center gap-2">
                        <Cpu className={`w-3 h-3 ${isAiAnalyzing ? 'animate-pulse' : ''}`}/> AI Agent
                    </button>
                    <button onClick={handleSave} className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200 flex items-center gap-2">
                        <Activity className="w-3 h-3"/> Save
                    </button>
                </div>
            </div>
            
            {/* Habits Grid */}
            <div className="grid grid-cols-2 gap-3 mt-4">
                {DEFAULT_HABITS.map(habit => {
                    const isActive = entry.habits?.[habit.id] || false;
                    const Icon = CoreEngine ? CoreEngine.getIconComponent(habit.icon) : Activity;
                    return (
                        <button key={habit.id} onClick={() => setEntry({ ...entry, habits: { ...entry.habits, [habit.id]: !isActive } })}
                            className={`p-4 rounded-2xl border transition-all flex items-center justify-between shadow-sm ${isActive ? 'bg-slate-800 border-slate-800 text-white' : 'bg-white border-slate-100 text-slate-500 hover:bg-slate-50'}`}>
                            <span className="text-xs font-bold">{habit.label}</span>
                            <Icon className={`w-5 h-5 ${isActive ? 'opacity-100' : 'opacity-20'}`} />
                        </button>
                    );
                })}
            </div>

            {/* Sliders */}
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-5 mt-4">
                {['mood', 'focus', 'energy'].map(k => (
                    <div key={k} className="flex items-center gap-4">
                        <label className="w-16 text-xs font-bold text-slate-400 uppercase">{k}</label>
                        <input type="range" min="0" max="10" value={entry[k]} onChange={e => setEntry({...entry, [k]: parseInt(e.target.value)})} className="flex-1 h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-500"/>
                        <span className="w-6 text-right text-sm font-bold text-indigo-600">{entry[k]}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};