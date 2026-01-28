'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
    Layers, PenTool, List as ListIcon, 
    Terminal, Cpu, Filter, CheckCircle, ArrowRight, Zap, TrendingUp, Clock, Upload 
} from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';
import { NeuralGraph } from '@/components/NeuralGraph';

// MOCK_LOGS 定義
const MOCK_LOGS = [
  { date: '2024-01-28', note: 'Project LifeOS: Fix Vercel deploy #coding', metrics: { mood: 6, focus: 8, energy: 7, deepWork: 4 }, graphSeeds: { tags: ['coding', 'project'], links: [] }, habits: { h4: true }, isSignal: false },
  { date: '2024-01-29', note: 'Family dinner at Taichung #life', metrics: { mood: 9, focus: 3, energy: 8, deepWork: 0 }, graphSeeds: { tags: ['life', 'family'], links: [] }, habits: {}, isSignal: false },
  { date: '2024-01-30', note: 'Deep work session on AI core logic #coding - [ ] Refactor core.ts', metrics: { mood: 7, focus: 9, energy: 6, deepWork: 6 }, graphSeeds: { tags: ['coding', 'ai'], links: [] }, habits: { h1: true, h4: true }, isSignal: true },
];

const safeConfig = { habits: DEFAULT_HABITS || [] };

export default function Home() {
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list'>('capture');
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
  const [aiThinkingLogs, setAiThinkingLogs] = useState<string[]>([]);
  
  const [entry, setEntry] = useState<any>({ 
      date: '', 
      note: '', 
      mood: 5, focus: 5, energy: 5, deepWork: 0,
      habits: {} 
  });
  
  const [detectedTasks, setDetectedTasks] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [historyPage, setHistoryPage] = useState(1);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Hydration mismatch fix
  useEffect(() => {
      setEntry((prev: any) => ({ ...prev, date: new Date().toISOString().split('T')[0] }));
      const saved = localStorage.getItem('life_os_logs_v8_0');
      if (saved) {
          try {
              setLogs(JSON.parse(saved));
          } catch(e) { console.error("Load failed", e); }
      }
  }, []);

  useEffect(() => {
      if (logs !== MOCK_LOGS) {
          localStorage.setItem('life_os_logs_v8_0', JSON.stringify(logs));
      }
  }, [logs]);

  // --- [Feature] JSON Import Logic ---
  const handleImportClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (ev) => {
          try {
              const content = ev.target?.result as string;
              const json = JSON.parse(content);
              
              // [Fix] 這裡加入明確的型別定義 : any[]
              let newLogs: any[] = [];
              
              if (Array.isArray(json)) {
                  newLogs = json;
              } else if (json.logs && Array.isArray(json.logs)) {
                  newLogs = json.logs;
              } else {
                  throw new Error("Invalid JSON format");
              }

              setLogs(prev => {
                  const existingDates = new Set(prev.map(l => l.date));
                  const filteredNew = newLogs.filter((l: any) => !existingDates.has(l.date));
                  const merged = [...prev, ...filteredNew].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
                  return merged;
              });
              
              alert(`✅ 成功匯入 ${newLogs.length} 筆紀錄`);
          } catch (err) {
              console.error(err);
              alert("❌ 匯入失敗：檔案格式錯誤");
          }
      };
      reader.readAsText(file);
      e.target.value = '';
  };

  const handleSaveLog = (newLog: any) => {
    const seeds = CoreEngine && CoreEngine.parseGraphSeeds 
        ? CoreEngine.parseGraphSeeds(entry.note) 
        : { tags: [], links: [] };

    const logToSave = newLog || {
        ...entry,
        graphSeeds: seeds
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
  };

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => { alert(msg); };

  const handleAIParse = async () => {
    const text = entry.note;
    if (!text) { showToast("❌ 請先輸入內容", "error"); return; }
    
    if (!CoreEngine || !CoreEngine.parseGraphSeeds) { 
        showToast("❌ 核心引擎未載入", "error"); 
        return; 
    }

    setIsAiAnalyzing(true);
    setAiThinkingLogs(["Initializing text parser..."]);
    const wait = (ms: number) => new Promise(r => setTimeout(r, ms));

    try {
        await wait(500);
        setAiThinkingLogs(prev => [...prev, "Reading context..."]);
        
        const mood = text.match(/(?:Mood|心情)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const focus = text.match(/(?:Focus|專注)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const energy = text.match(/(?:Energy|能量)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const deep = text.match(/(?:Deep|Reading|深度)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const dateMatch = text.match(/(?:Date|日期|^#\s*\[?)?\s*(\d{4}-\d{2}-\d{2})/m);
        
        const targetDate = dateMatch ? dateMatch[1] : entry.date;
        const graphMatch = text.match(/(?:Graph|Connections|關聯)(?:[\s:：]*)(?:[\r\n]+)([\s\S]*?)(?:$|^#)/mi);
        const graphContent = graphMatch ? graphMatch[1].trim() : '';
        const seeds = CoreEngine.parseGraphSeeds(graphContent || text);
        
        let detectedFocus = focus ? parseInt(focus[1]) : entry.focus;
        if (text.includes('URGENT') || text.includes('TODO')) {
            detectedFocus = Math.max(detectedFocus || 5, 8);
        }

        let detectedHabits = { ...entry.habits };
        safeConfig.habits.forEach(h => {
            if (text.toLowerCase().includes(h.id) || text.includes(h.label.split(' ')[0].toLowerCase())) {
                detectedHabits[h.id] = true;
            }
        });

        let tasks: string[] = [];
        const taskRegex = /-\s*\[\s*\]\s*(.*)/g;
        let match;
        while ((match = taskRegex.exec(text)) !== null) {
            tasks.push(match[1]);
        }
        setDetectedTasks(tasks);

        setEntry((prev: any) => ({
            ...prev,
            date: targetDate,
            mood: mood ? parseInt(mood[1]) : prev.mood,
            focus: detectedFocus,
            energy: energy ? parseInt(energy[1]) : prev.energy,
            deepWork: deep ? parseInt(deep[1]) : prev.deepWork,
            habits: detectedHabits,
            graphSeeds: { tags: seeds.tags, links: seeds.links, content: graphContent } 
        }));
        showToast(`🪄 AI 分析完成`);

    } catch (error: any) {
        console.error(error);
        setAiThinkingLogs(prev => [...prev, `❌ Error: ${error.message}`]);
    } finally {
        setIsAiAnalyzing(false);
    }
  };

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
                    placeholder="# 輸入你的想法...\n> Agent 會幫你整理成 Project 與 Life 雙軌"
                    className="w-full h-48 p-4 bg-slate-900 border border-slate-700 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-500 outline-none resize-none leading-relaxed text-slate-200 placeholder:text-slate-600"
                />
                {detectedTasks.length > 0 && (
                    <div className="mt-4 p-3 bg-indigo-900/30 border border-indigo-500/30 rounded-xl">
                        <div className="text-xs font-bold text-indigo-300 mb-2 flex items-center gap-2"><CheckCircle size={12}/> Extracted Tasks</div>
                        <ul className="space-y-1">
                            {detectedTasks.map((t, i) => (
                                <li key={i} className="text-xs text-slate-300 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>{t}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
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
      case 'graph':
        return (
          <div className="h-full flex flex-col">
            <div className="flex-1 relative overflow-hidden rounded-2xl border border-slate-800 bg-[#0b1120]">
               <NeuralGraph logs={logs} onNodeClick={(node: any) => alert(`Clicked: ${node.label}`)} />
            </div>
            <div className="p-4 text-center text-slate-500 text-xs">
               <Activity className="w-3 h-3 inline mr-1"/> 
               目前共有 {logs.length} 個節點正在運作
            </div>
          </div>
        );
      case 'list':
        const filteredLogs = logs.filter(log => (log.note + log.date).toLowerCase().includes(searchTerm.toLowerCase()));
        const ITEMS_PER_PAGE_LIST = 5;
        const startIndex = (historyPage - 1) * ITEMS_PER_PAGE_LIST;
        const currentLogs = filteredLogs.slice(startIndex, startIndex + ITEMS_PER_PAGE_LIST);
        const totalPages = Math.ceil(filteredLogs.length / ITEMS_PER_PAGE_LIST);

        return (
            <div className="h-full flex flex-col pb-20">
                <div className="flex justify-between items-center mb-6 px-2">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2"><ListIcon className="text-indigo-400" /> History</h2>
                    <div className="flex gap-2">
                        <input type="text" placeholder="Filter..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="bg-slate-800 rounded-full text-xs text-white border border-slate-700 px-4 py-2 w-24 focus:w-32 transition-all outline-none"/>
                        {/* 匯入按鈕 UI */}
                        <button onClick={handleImportClick} className="bg-slate-800 hover:bg-slate-700 text-slate-300 p-2 rounded-full border border-slate-700" title="匯入 JSON">
                            <Upload size={16}/>
                        </button>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto space-y-4 px-2 custom-scrollbar">
                    {currentLogs.map((log, i) => (
                        <div key={i} className="bg-[#1e293b] p-4 rounded-xl border border-slate-700">
                            <div className="flex justify-between mb-2">
                                <span className="text-white font-bold">{log.date}</span>
                                <span className="text-xs text-slate-400">Mood: {log.metrics?.mood}</span>
                            </div>
                            <p className="text-sm text-slate-300 line-clamp-2">{log.note}</p>
                        </div>
                    ))}
                </div>
                {totalPages > 1 && (
                    <div className="flex justify-center gap-2 mt-4">
                        {Array.from({ length: totalPages }).map((_, i) => (
                            <button key={i} onClick={() => setHistoryPage(i + 1)} className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${historyPage === i + 1 ? 'bg-indigo-600 text-white shadow-lg' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>{i + 1}</button>
                        ))}
                    </div>
                )}
            </div>
        );
    }
  };

  return (
    <div className="max-w-md mx-auto h-screen bg-[#0f172a] flex flex-col font-sans text-slate-200 relative shadow-2xl overflow-hidden">
        {/* 隱藏的檔案上傳 Input */}
        <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
            accept=".json"
        />

        <header className="px-6 py-4 bg-[#0f172a]/90 backdrop-blur z-20 flex justify-between items-center border-b border-slate-800 sticky top-0">
            <h1 className="text-lg font-black tracking-tight text-white">LifeOS <span className="text-indigo-400 text-xs align-top border border-indigo-500/30 px-1 rounded">v2.0 Cloud</span></h1>
            <div className="flex items-center gap-2">
                <button onClick={handleImportClick} className="text-slate-500 hover:text-white transition-colors p-1" title="Import Data">
                    <Upload size={18}/>
                </button>
                <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center"><span className="text-xs font-bold text-indigo-300">LH</span></div>
            </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 relative z-10 custom-scrollbar">
            {renderContent()}
        </main>
        <nav className="absolute bottom-6 left-6 right-6 h-16 bg-[#1e293b]/90 backdrop-blur-md rounded-2xl border border-slate-700/50 shadow-2xl flex justify-around items-center px-2 z-50">
            <button onClick={() => setActiveTab('capture')} className={`p-2 ${activeTab === 'capture' ? 'text-indigo-400' : 'text-slate-500'}`}><PenTool size={20}/></button>
            <button onClick={() => setActiveTab('graph')} className={`p-2 ${activeTab === 'graph' ? 'text-indigo-400' : 'text-slate-500'}`}><Layers size={20}/></button>
            <button onClick={() => setActiveTab('list')} className={`p-2 ${activeTab === 'list' ? 'text-indigo-400' : 'text-slate-500'}`}><ListIcon size={20}/></button>
        </nav>
    </div>
  );
}