// 檔案: frontend-body/components/CaptureView.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { PenTool, Cpu, Activity, Terminal, CheckCircle, AlertTriangle } from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';
import { cortex } from '@/lib/api/client'; // [Fix 1] 引入神經束 (連線到 Python 後端)

export const CaptureView = ({ onSave }: { onSave: (log: any) => void }) => {
  const [entry, setEntry] = useState({ date: '', note: '', mood: 5, focus: 5, energy: 5, deepWork: 0, habits: {} });
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
  const [aiThinkingLogs, setAiThinkingLogs] = useState<string[]>([]);
  const [detectedTasks, setDetectedTasks] = useState<string[]>([]);

  useEffect(() => {
    setEntry((prev: any) => ({ ...prev, date: new Date().toISOString().split('T') }));
  }, []);

  const handleAIParse = async () => {
    if (!entry.note) return alert("❌ 請輸入內容");
    
    setIsAiAnalyzing(true);
    setAiThinkingLogs(["連線神經網絡...", "正在讀取脈絡..."]);

    try {
      // [V3.1 Fix] 這裡原本是 '/api/ingest'，現在改為指向 Python 大腦的 Rewrite 路徑
      // 路徑對應： /api/py/ingest -> http://localhost:8001/api/v1/ingest
      const response = await fetch('/api/py/ingest', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: entry.note,
            date: entry.date
        })
    });

      // 檢查回應狀態
      const contentType = response.headers.get("content-type");
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Brain Error:", errorText);
        throw new Error(`Cortex 回應錯誤 (${response.status})`);
      }

      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Cortex 回傳了非 JSON 格式 (可能是 500 錯誤頁面)");
      }

      const result = await response.json();
      
      // 兼容 Python 回傳格式 (Python 通常直接回傳 data，或包含在 success 欄位)
      // 假設 backend 回傳: { success: true, data: { ... }, model: ... }
      const aiData = result.data || result; 

      setAiThinkingLogs(prev => [...prev, "✅ 分析完成", `Model: ${result.model || 'Gemini-2.0'}`]);

      // 更新 UI 狀態
      const metrics = aiData.meta?.metrics || {};
      setEntry((prev: any) => ({
        ...prev,
        note: aiData.markdown_body || prev.note, // 更新為 AI 整理後的 Markdown
        mood: metrics.mood ?? prev.mood,
        focus: metrics.focus ?? prev.focus,
        energy: metrics.energy ?? prev.energy,
      }));

      if (aiData.tasks && Array.isArray(aiData.tasks)) {
        setDetectedTasks(aiData.tasks.map((t: any) => t.title || t.task)); // 兼容 title 或 task 欄位
        setAiThinkingLogs(prev => [...prev, `⚡ 提取了 ${aiData.tasks.length} 個行動`]);
      }

    } catch (e: any) {
      console.error("AI Error:", e);
      setAiThinkingLogs(prev => [...prev, `❌ 錯誤: ${e.message}`]);
    } finally {
      setIsAiAnalyzing(false);
    }
  };

  const handleSave = () => {
    const seeds = CoreEngine ? CoreEngine.parseGraphSeeds(entry.note) : { tags: [], links: [] };
    onSave({ ...entry, graphSeeds: seeds });
    
    // Reset
    setEntry({ 
      date: new Date().toISOString().split('T')[0], // 👈 關鍵修正：加上 
      note: '', 
      mood: 5, 
      focus: 5, 
      energy: 5, 
      deepWork: 0, 
      habits: {} 
    });
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
          value={entry.note} 
          onChange={e => setEntry({...entry, note: e.target.value})} 
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
          <button 
            onClick={handleAIParse} 
            disabled={isAiAnalyzing}
            className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 transition-colors flex items-center gap-2"
          >
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
          const isActive = (entry.habits as any)?.[habit.id] || false;
          const Icon = CoreEngine ? CoreEngine.getIconComponent(habit.icon) : Activity;
          return (
            <button 
              key={habit.id} 
              onClick={() => setEntry({ ...entry, habits: { ...entry.habits, [habit.id]: !isActive } })}
              className={`p-4 rounded-2xl border transition-all flex items-center justify-between shadow-sm ${isActive ? 'bg-slate-800 border-slate-800 text-white' : 'bg-white border-slate-100 text-slate-500 hover:bg-slate-50'}`}
            >
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
            <input 
              type="range" min="0" max="10" 
              value={(entry as any)[k]} 
              onChange={e => setEntry({...entry, [k]: parseInt(e.target.value)})} 
              className="flex-1 h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <span className="w-6 text-right text-sm font-bold text-indigo-600">{(entry as any)[k]}</span>
          </div>
        ))}
      </div>
    </div>
  );
};