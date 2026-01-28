// 檔案位置: components/CaptureView.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { PenTool, Cpu, Activity, Terminal, CheckCircle } from 'lucide-react';
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

    const handleAIParse = async () => {
        if (!entry.note) return alert("❌ 請輸入內容");
        if (!CoreEngine) return alert("❌ 核心引擎未載入");

        setIsAiAnalyzing(true);
        setAiThinkingLogs(["Initializing text parser..."]);
        const wait = (ms: number) => new Promise(r => setTimeout(r, ms));

        try {
            await wait(500);
            setAiThinkingLogs(prev => [...prev, "Reading context..."]);
            
            // 模擬 AI 分析過程 (Regex)
            const mood = entry.note.match(/(?:Mood|心情)[\s\S]*?(\d+(?:\.\d+)?)/i);
            const focus = entry.note.match(/(?:Focus|專注)[\s\S]*?(\d+(?:\.\d+)?)/i);
            const energy = entry.note.match(/(?:Energy|能量)[\s\S]*?(\d+(?:\.\d+)?)/i);
            const dateMatch = entry.note.match(/(?:Date|日期|^#\s*\[?)?\s*(\d{4}-\d{2}-\d{2})/m);
            const targetDate = dateMatch ? dateMatch[1] : entry.date;
            
            const graphMatch = entry.note.match(/(?:Graph|Connections|關聯)(?:[\s:：]*)(?:[\r\n]+)([\s\S]*?)(?:$|^#)/mi);
            const seeds = CoreEngine.parseGraphSeeds(graphMatch ? graphMatch[1].trim() : entry.note);
            
            if(seeds.tags.length) setAiThinkingLogs(prev => [...prev, `Identified Tags: ${seeds.tags.join(', ')}`]);

            // Tasks
            let tasks: string[] = [];
            const taskRegex = /-\s*\[\s*\]\s*(.*)/g;
            let match;
            while ((match = taskRegex.exec(entry.note)) !== null) tasks.push(match[1]);
            setDetectedTasks(tasks);
            if(tasks.length) setAiThinkingLogs(prev => [...prev, `⚡ Extracted ${tasks.length} actionable tasks`]);

            await wait(400);
            setAiThinkingLogs(prev => [...prev, "✅ Analysis Complete."]);
            
            setEntry((prev: any) => ({
                ...prev,
                date: targetDate,
                mood: mood ? parseInt(mood[1]) : prev.mood,
                focus: focus ? parseInt(focus[1]) : prev.focus,
                energy: energy ? parseInt(energy[1]) : prev.energy,
                graphSeeds: seeds
            }));

        } catch (e: any) {
            setAiThinkingLogs(prev => [...prev, `Error: ${e.message}`]);
        } finally {
            setIsAiAnalyzing(false);
        }
    };

    const handleSave = () => {
        const seeds = CoreEngine.parseGraphSeeds(entry.note);
        onSave({ ...entry, graphSeeds: seeds });
        setEntry({ date: new Date().toISOString().split('T')[0], note: '', mood: 5, focus: 5, energy: 5, deepWork: 0, habits: {} });
        setDetectedTasks([]);
        setAiThinkingLogs([]);
    };

    return (
        <div className="h-full flex flex-col justify-center max-w-lg mx-auto w-full pb-20">
            <h2 className="text-2xl font-bold text-white mb-6 px-4 flex items-center gap-2">
               <PenTool className="text-indigo-400" /> Capture Flow
            </h2>
            
            {/* AI Terminal */}
            {(isAiAnalyzing || aiThinkingLogs.length > 0) && (
                <div className="mb-4 bg-slate-900 rounded-xl p-4 border border-indigo-500/30 shadow-lg animate-fade-in">
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

            <div className="bg-[#1e293b] p-6 rounded-3xl shadow-lg border border-slate-700">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-bold text-slate-300 flex items-center gap-2">DAILY LOG</span>
                    <input type="date" value={entry.date} onChange={e => setEntry({...entry, date: e.target.value})} className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1 text-sm font-mono outline-none text-white"/>
                </div>
                <textarea 
                    value={entry.note} onChange={e => setEntry({...entry, note: e.target.value})}
                    placeholder="# 輸入想法..."
                    className="w-full h-48 p-4 bg-slate-900 border border-slate-700 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-500 outline-none resize-none leading-relaxed text-slate-200 placeholder:text-slate-600"
                />
                
                {detectedTasks.length > 0 && (
                    <div className="mt-4 p-3 bg-indigo-900/30 border border-indigo-500/30 rounded-xl">
                        <div className="text-xs font-bold text-indigo-300 mb-2 flex items-center gap-2"><CheckCircle size={12}/> Extracted Tasks</div>
                        <ul className="space-y-1">
                            {detectedTasks.map((t, i) => <li key={i} className="text-xs text-slate-300 flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>{t}</li>)}
                        </ul>
                    </div>
                )}

                <div className="flex justify-end gap-2 mt-4">
                    <button onClick={handleAIParse} disabled={isAiAnalyzing} className={`px-4 py-2 rounded-xl bg-slate-700 text-indigo-300 text-xs font-bold hover:bg-slate-600 transition-colors flex items-center gap-2 border border-slate-600 ${isAiAnalyzing ? 'opacity-50 cursor-not-allowed' : ''}`}>
                        <Cpu className={`w-3 h-3 ${isAiAnalyzing ? 'animate-pulse' : ''}`}/> 
                        {isAiAnalyzing ? "Analyzing..." : "AI Agent"}
                    </button>
                    <button onClick={handleSave} className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/30 flex items-center gap-2">
                        <Activity className="w-3 h-3"/> Save
                    </button>
                </div>
            </div>
            
            <div className="bg-[#1e293b] p-6 rounded-3xl shadow-lg border border-slate-700 space-y-4 mt-4">
                {['mood', 'focus', 'energy'].map(k => (
                    <div key={k} className="flex items-center gap-4">
                        <label className="w-16 text-xs font-bold text-slate-400 uppercase">{k}</label>
                        <input type="range" min="0" max="10" value={entry[k]} onChange={e => setEntry({...entry, [k]: parseInt(e.target.value)})} className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"/>
                        <span className="w-6 text-right text-sm font-bold text-indigo-400">{entry[k]}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};