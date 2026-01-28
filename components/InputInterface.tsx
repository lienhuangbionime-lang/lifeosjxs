// 檔案位置: src/components/InputInterface.tsx
"use client";
import React, { useState } from 'react';
import { Edit3, Cpu, Save, Hash, Link as LinkIcon, GitGraph } from 'lucide-react';
import { DEFAULT_HABITS, CoreEngine } from '@/lib/ai/core';

export const InputInterface = ({ onSaveEntry }: { onSaveEntry: (data: any) => void }) => {
    const [note, setNote] = useState("");
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [isProcessing, setIsProcessing] = useState(false);
    
    // UI State for sliders (Metrics)
    const [metrics, setMetrics] = useState({ mood: 5, focus: 5, energy: 5, deepWork: 0 });

    const handleAIAgent = async () => {
        setIsProcessing(true);
        try {
            // [Cloud Agent Call] 呼叫後端 API
            const res = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: note, date })
            });
            const result = await res.json();
            
            if (result.success) {
                // Agent 回傳整理好的資料，我們更新前端
                setNote(result.data.markdown_body);
                // 這裡可以選擇是否自動更新 Metrics
                alert("Agent: 思考完畢，資料已結構化。");
            } else {
                alert("Agent Error: " + result.error);
            }
        } catch (e) {
            console.error(e);
            alert("Network Error");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleLocalSave = () => {
        // 先做本地更新，讓 UI 馬上有反應
        onSaveEntry({
            date,
            note,
            metrics,
            graphSeeds: CoreEngine.parseGraphSeeds(note)
        });
    };

    return (
        <div className="space-y-6 pb-24 animate-fade-in">
            <div className="bg-[#1e293b] p-6 rounded-3xl shadow-lg border border-slate-700">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-bold text-slate-300 flex items-center gap-2"><Edit3 className="w-4 h-4"/> DAILY LOG</span>
                    <input type="date" value={date} onChange={e => setDate(e.target.value)} className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1 text-sm font-mono outline-none text-white"/>
                </div>
                
                <textarea 
                    value={note} onChange={e => setNote(e.target.value)}
                    placeholder="# 輸入你的想法...\n> Agent 會幫你整理成 Project 與 Life 雙軌"
                    className="w-full h-48 p-4 bg-slate-900 border border-slate-700 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-500 outline-none resize-none leading-relaxed text-slate-200 placeholder:text-slate-600"
                />

                <div className="flex justify-end gap-2 mt-4">
                    <button onClick={handleAIAgent} disabled={isProcessing} className="px-4 py-2 rounded-xl bg-slate-700 text-indigo-300 text-xs font-bold hover:bg-slate-600 transition-colors flex items-center gap-2 border border-slate-600">
                        <Cpu className={`w-3 h-3 ${isProcessing ? 'animate-pulse' : ''}`}/> 
                        {isProcessing ? "Agent Working..." : "Call Agent"}
                    </button>
                    <button onClick={handleLocalSave} className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/30 flex items-center gap-2">
                        <Save className="w-3 h-3"/> Save
                    </button>
                </div>
            </div>
            
            {/* Metrics Sliders */}
            <div className="bg-[#1e293b] p-6 rounded-3xl shadow-lg border border-slate-700 space-y-4">
                {['mood', 'focus', 'energy'].map(k => (
                    <div key={k} className="flex items-center gap-4">
                        <label className="w-16 text-xs font-bold text-slate-400 uppercase">{k}</label>
                        <input 
                            type="range" min="0" max="10" 
                            value={(metrics as any)[k]} 
                            onChange={e => setMetrics({...metrics, [k]: parseInt(e.target.value)})}
                            className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                        />
                        <span className="w-6 text-right text-sm font-bold text-indigo-400">{(metrics as any)[k]}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
