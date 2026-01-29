'use client';

import React, { useState, useEffect } from 'react';
import { PenTool, Cpu, Activity, Terminal, CheckCircle } from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';

export const CaptureView = ({ onSave }: { onSave: (log: any) => void }) => {
    // ... (狀態與邏輯保持不變，請複製之前的 handleAIParse, handleSave 等邏輯) ...
    // 為了節省篇幅，這裡僅展示 UI (Render) 部分的重大修改
    
    // 請保留原有的 useState, useEffect, handleAIParse, handleSave
    // ... (State & Handlers) ...
    const [entry, setEntry] = useState<any>({ 
        date: '', note: '', mood: 5, focus: 5, energy: 5, deepWork: 0, habits: {} 
    });
    const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
    const [aiThinkingLogs, setAiThinkingLogs] = useState<string[]>([]);
    const [detectedTasks, setDetectedTasks] = useState<string[]>([]);

    useEffect(() => { setEntry((prev: any) => ({ ...prev, date: new Date().toISOString().split('T')[0] })); }, []);

    const handleAIParse = async () => { /* ...請複製之前的邏輯... */ 
        setIsAiAnalyzing(true);
        // ... (模擬邏輯)
        setTimeout(() => setIsAiAnalyzing(false), 1000);
    };
    
    const handleSave = () => { onSave({...entry, graphSeeds: CoreEngine.parseGraphSeeds(entry.note)}); };

    return (
        // [Fix] 這裡加入 overflow-y-auto 與 pb-24 確保底部不被遮擋
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                   <PenTool className="text-indigo-500" /> Capture Flow
                </h2>
                <p className="text-slate-400 text-xs mt-1">紀錄當下，讓 AI 幫你整理結構</p>
            </div>
            
            {/* AI Terminal (保持深色以強調科技感) */}
            {(isAiAnalyzing || aiThinkingLogs.length > 0) && (
                <div className="mb-6 bg-slate-900 rounded-2xl p-4 shadow-xl border border-slate-800">
                    {/* ... Terminal UI 保持不變 ... */}
                    <div className="text-emerald-400 font-mono text-xs">AI Processing...</div>
                </div>
            )}

            {/* Input Card - [Fix] 改為柔和白色風格 */}
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
                
                {/* 任務偵測區 */}
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
            
            {/* Habits Grid - [Fix] 柔和風格 */}
            <div className="grid grid-cols-2 gap-3 mt-4">
                {DEFAULT_HABITS.map(habit => {
                    const isActive = entry.habits?.[habit.id] || false;
                    const Icon = CoreEngine.getIconComponent(habit.icon);
                    return (
                        <button key={habit.id} onClick={() => setEntry({ ...entry, habits: { ...entry.habits, [habit.id]: !isActive } })}
                            className={`p-4 rounded-2xl border transition-all flex items-center justify-between shadow-sm ${isActive ? 'bg-slate-800 border-slate-800 text-white' : 'bg-white border-slate-100 text-slate-500 hover:bg-slate-50'}`}>
                            <span className="text-xs font-bold">{habit.label}</span>
                            <Icon className={`w-5 h-5 ${isActive ? 'opacity-100' : 'opacity-20'}`} />
                        </button>
                    );
                })}
            </div>

            {/* Sliders - [Fix] 柔和風格 */}
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