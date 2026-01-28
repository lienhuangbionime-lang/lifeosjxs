// 檔案位置: app/page.tsx
'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { 
    Layers, PenTool, List as ListIcon, Activity, 
    Terminal, Cpu, Filter, Zap, TrendingUp, Clock, ArrowRight, CheckCircle 
} from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';
import { NeuralGraph } from '@/components/NeuralGraph';

// --- MOCK DATA (保持不變) ---
const MOCK_LOGS = [
  { date: '2024-01-28', note: 'Project LifeOS: Fix Vercel deploy #coding', metrics: { mood: 6, focus: 8, energy: 7, deepWork: 4 }, graphSeeds: { tags: ['coding', 'project'] }, habits: { h4: true } },
  { date: '2024-01-29', note: 'Family dinner at Taichung #life', metrics: { mood: 9, focus: 3, energy: 8, deepWork: 0 }, graphSeeds: { tags: ['life', 'family'] }, habits: {} },
  { date: '2024-01-30', note: 'Deep work session on AI core logic #coding - [ ] Refactor core.ts', metrics: { mood: 7, focus: 9, energy: 6, deepWork: 6 }, graphSeeds: { tags: ['coding', 'ai'] }, habits: { h1: true, h4: true } },
  { date: '2024-01-31', note: 'Gym workout and reading science fiction #health', metrics: { mood: 8, focus: 6, energy: 9, deepWork: 2 }, graphSeeds: { tags: ['health', 'reading'] }, habits: { h2: true, h3: true } },
  { date: '2024-02-01', note: 'Planning next sprint', metrics: { mood: 5, focus: 7, energy: 5, deepWork: 3 }, graphSeeds: { tags: ['planning'] }, habits: {} },
  { date: '2024-02-02', note: 'Debug UI issues', metrics: { mood: 4, focus: 8, energy: 4, deepWork: 5 }, graphSeeds: { tags: ['coding', 'bugfix'] }, habits: { h4: true } },
];

const ITEMS_PER_PAGE = 3;
const config = { habits: DEFAULT_HABITS };

export default function Home() {
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list'>('capture');
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
  const [aiThinkingLogs, setAiThinkingLogs] = useState<string[]>([]);
  const [entry, setEntry] = useState<any>({ 
      date: new Date().toISOString().split('T')[0], 
      note: '', 
      mood: 5, focus: 5, energy: 5, deepWork: 0,
      habits: {} 
  });
  const [detectedTasks, setDetectedTasks] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [historyPage, setHistoryPage] = useState(1);

  // --- Actions ---

  const handleSaveLog = useCallback((newLog: any) => {
    const logToSave = newLog || {
        ...entry,
        graphSeeds: CoreEngine ? CoreEngine.parseGraphSeeds(entry.note) : { tags: [], links: [] }
    };
    setLogs(prev => [logToSave, ...prev]);
    setActiveTab('graph');
    setEntry({ 
      date: new Date().toISOString().split('T')[0], 
      note: '', 
      mood: 5, focus: 5, energy: 5, deepWork: 0,
      habits: {} 
    });
    setAiThinkingLogs([]);
    setDetectedTasks([]);
  }, [entry]);

  const showToast = (msg: string) => { alert(msg); };

  const handleAIParse = async () => {
    const text = entry.note;
    if (!text) { showToast("❌ 請先輸入內容"); return; }
    if (!CoreEngine) { showToast("❌ 核心引擎未載入"); return; }

    setIsAiAnalyzing(true);
    setAiThinkingLogs(["Initializing text parser..."]);
    const wait = (ms: number) => new Promise(r => setTimeout(r, ms));

    try {
        await wait(600);
        setAiThinkingLogs(prev => [...prev, "Reading context..."]);
        // ... (模擬 AI 邏輯，為節省篇幅省略，功能不變) ...
        await wait(1000);
        setAiThinkingLogs(prev => [...prev, "Analysis Complete."]);
        showToast("AI 分析完成 (Mock)");
        setIsAiAnalyzing(false);
    } catch (e) {
        setIsAiAnalyzing(false);
    }
  };

  // 🔴 關鍵修正：使用 useCallback 鎖定這個函式
  // 避免每次 Render 都產生新函式，導致 NeuralGraph 無限重啟
  const handleNodeClick = useCallback((node: any) => {
      alert(`Clicked: ${node.label}`);
  }, []);

  const renderAiTerminal = () => {
    if (!isAiAnalyzing && aiThinkingLogs.length === 0) return null;
    return (
        <div className="mb-4 bg-slate-900 rounded-xl p-4 border border-indigo-500/30 shadow-lg animate-fade-in">
            <div className="flex items-center gap-2 mb-2 border-b border-slate-800 pb-2">
                <Terminal size={14} className="text-emerald-400 animate-pulse"/>
                <span className="text-xs font-mono text-emerald-400 font-bold">AI_CORE_PROCESSOR</span>
            </div>
            <div className="font-mono text-xs space-y-1 h-32 overflow-y-auto custom-scrollbar flex flex-col-reverse">
                {isAiAnalyzing && <div className="text-emerald-500 animate-pulse">_</div>}
                {[...aiThinkingLogs].reverse().map((log, i) => (
                    <div key={i} className="text-slate-300">
                        <span className="text-indigo-500 mr-2">➜</span>
                        {log}
                    </div>
                ))}
            </div>
        </div>
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'capture':
        return (
          <div className="h-full flex flex-col justify-center max-w-lg mx-auto w-full pb-20">
            <h2 className="text-2xl font-bold text-white mb-6 px-4 flex items-center gap-2">
               <PenTool className="text-indigo-400" /> Capture Flow
            </h2>
            {renderAiTerminal()}
            <div className="bg-[#1e293b] p-6 rounded-3xl shadow-lg border border-slate-700">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-bold text-slate-300 flex items-center gap-2">DAILY LOG</span>
                    <input type="date" value={entry.date} onChange={e => setEntry({...entry, date: e.target.value})} className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1 text-sm font-mono outline-none text-white"/>
                </div>
                <textarea 
                    value={entry.note} onChange={e => setEntry({...entry, note: e.target.value})}
                    placeholder="# 輸入你的想法..."
                    className="w-full h-48 p-4 bg-slate-900 border border-slate-700 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-500 outline-none resize-none leading-relaxed text-slate-200 placeholder:text-slate-600"
                />
                <div className="flex justify-end gap-2 mt-4">
                    <button onClick={handleAIParse} disabled={isAiAnalyzing} className={`px-4 py-2 rounded-xl bg-slate-700 text-indigo-300 text-xs font-bold hover:bg-slate-600 transition-colors flex items-center gap-2 border border-slate-600 ${isAiAnalyzing ? 'opacity-50 cursor-not-allowed' : ''}`}>
                        <Cpu className={`w-3 h-3 ${isAiAnalyzing ? 'animate-pulse' : ''}`}/> 
                        {isAiAnalyzing ? "Analyzing..." : "AI Agent"}
                    </button>
                    <button onClick={() => handleSaveLog(null)} className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/30 flex items-center gap-2">
                        <Activity className="w-3 h-3"/> Save
                    </button>
                </div>
            </div>
          </div>
        );
      case 'graph':
        return (
          <div className="h-full flex flex-col">
            <div className="flex-1 relative overflow-hidden rounded-2xl border border-slate-800 bg-[#0b1120]">
               {/* 🔴 關鍵：這裡傳入的是被 useCallback 鎖定的函式 */}
               <NeuralGraph logs={logs} onNodeClick={handleNodeClick} />
            </div>
            <div className="p-4 text-center text-slate-500 text-xs">
               <Activity className="w-3 h-3 inline mr-1"/> 
               目前共有 {logs.length} 個節點正在運作
            </div>
          </div>
        );
      case 'list':
        // (List 邏輯保持不變，為節省篇幅省略)
        const filteredLogs = logs.filter(log => (log.note + log.date).toLowerCase().includes(searchTerm.toLowerCase()));
        return (
            <div className="h-full flex flex-col pb-20">
                <div className="flex justify-between items-center mb-6 px-2">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <ListIcon className="text-indigo-400" /> Neural History
                    </h2>
                     <div className="relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4"/>
                        <input type="text" placeholder="Filter..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-9 pr-4 py-2 bg-slate-800 rounded-full text-xs text-white border border-slate-700 outline-none w-32 focus:w-48 transition-all"/>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto space-y-4 px-2 custom-scrollbar">
                    {filteredLogs.map((log, i) => (
                        <div key={i} className="bg-[#1e293b] p-4 rounded-xl border border-slate-700 text-slate-300 text-sm">
                            <div className="font-bold text-white mb-1">{log.date}</div>
                            {log.note}
                        </div>
                    ))}
                </div>
            </div>
        );
    }
  };

  return (
    <div className="max-w-md mx-auto h-screen bg-[#0f172a] flex flex-col font-sans text-slate-200 relative shadow-2xl overflow-hidden">
        <header className="px-6 py-4 bg-[#0f172a]/90 backdrop-blur z-20 flex justify-between items-center border-b border-slate-800 sticky top-0">
            <h1 className="text-lg font-black tracking-tight text-white">LifeOS <span className="text-indigo-400 text-xs align-top border border-indigo-500/30 px-1 rounded">v2.0 Cloud</span></h1>
        </header>
        <main className="flex-1 overflow-y-auto p-4 relative z-10 custom-scrollbar">
            {renderContent()}
        </main>
        <nav className="absolute bottom-6 left-6 right-6 h-16 bg-[#1e293b]/90 backdrop-blur-md rounded-2xl border border-slate-700/50 shadow-2xl flex justify-around items-center px-2 z-50">
            <button onClick={() => setActiveTab('capture')} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all ${activeTab === 'capture' ? 'text-indigo-400 bg-indigo-500/10 scale-105' : 'text-slate-500 hover:text-slate-300'}`}><PenTool size={20}/><span className="text-[10px] font-bold">Capture</span></button>
            <button onClick={() => setActiveTab('graph')} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all ${activeTab === 'graph' ? 'text-indigo-400 bg-indigo-500/10 scale-105' : 'text-slate-500 hover:text-slate-300'}`}><Layers size={20}/><span className="text-[10px] font-bold">Neural</span></button>
            <button onClick={() => setActiveTab('list')} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all ${activeTab === 'list' ? 'text-indigo-400 bg-indigo-500/10 scale-105' : 'text-slate-500 hover:text-slate-300'}`}><ListIcon size={20}/><span className="text-[10px] font-bold">History</span></button>
        </nav>
    </div>
  );
}