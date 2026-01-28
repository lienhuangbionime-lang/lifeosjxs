// src/app/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { NeuralGraph } from '@/components/NeuralGraph';
import { InputInterface } from '@/components/InputInterface'; // Assuming you kept this component structure
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';
import { 
    Layers, PenTool, List as ListIcon, Calendar, Activity, 
    Terminal, Cpu, Filter, X, Zap, TrendingUp, Clock, AlertTriangle, ArrowRight 
} from 'lucide-react';

// --- MOCK DATA ---
const MOCK_LOGS = [
  { date: '2024-01-28', note: 'Project LifeOS: Fix Vercel deploy #coding', metrics: { mood: 6, focus: 8, energy: 7, deepWork: 4 }, graphSeeds: { tags: ['coding', 'project'] }, habits: { h4: true } },
  { date: '2024-01-29', note: 'Family dinner at Taichung #life', metrics: { mood: 9, focus: 3, energy: 8, deepWork: 0 }, graphSeeds: { tags: ['life', 'family'] }, habits: {} },
  { date: '2024-01-30', note: 'Deep work session on AI core logic #coding - [ ] Refactor core.ts', metrics: { mood: 7, focus: 9, energy: 6, deepWork: 6 }, graphSeeds: { tags: ['coding', 'ai'] }, habits: { h1: true, h4: true } },
  { date: '2024-01-31', note: 'Gym workout and reading science fiction #health', metrics: { mood: 8, focus: 6, energy: 9, deepWork: 2 }, graphSeeds: { tags: ['health', 'reading'] }, habits: { h2: true, h3: true } },
  { date: '2024-02-01', note: 'Planning next sprint', metrics: { mood: 5, focus: 7, energy: 5, deepWork: 3 }, graphSeeds: { tags: ['planning'] }, habits: {} },
  { date: '2024-02-02', note: 'Debug UI issues', metrics: { mood: 4, focus: 8, energy: 4, deepWork: 5 }, graphSeeds: { tags: ['coding', 'bugfix'] }, habits: { h4: true } },
];

const ITEMS_PER_PAGE = 3;

// Config for habits (matching DEFAULT_HABITS from core.ts)
const config = {
    habits: DEFAULT_HABITS
};

export default function Home() {
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list'>('capture');
  
  // --- AI State ---
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
  const [aiThinkingLogs, setAiThinkingLogs] = useState<string[]>([]);
  const [entry, setEntry] = useState<any>({ 
      date: new Date().toISOString().split('T')[0], 
      note: '', 
      mood: 5, focus: 5, energy: 5, deepWork: 0,
      habits: {} 
  });
  const [detectedTasks, setDetectedTasks] = useState<string[]>([]);

  // --- History State ---
  const [searchTerm, setSearchTerm] = useState('');
  const [historyPage, setHistoryPage] = useState(1);
  const [selectedEntry, setSelectedEntry] = useState<any>(null); // For future detail view

  // --- Actions ---

  const handleSaveLog = (newLog: any) => {
    // Merge new log with current state if passed from InputInterface
    // Or save the current 'entry' state
    const logToSave = newLog || {
        ...entry,
        graphSeeds: CoreEngine.parseGraphSeeds(entry.note)
    };
    
    setLogs(prev => [logToSave, ...prev]);
    setActiveTab('graph');
    
    // Reset entry
    setEntry({ 
      date: new Date().toISOString().split('T')[0], 
      note: '', 
      mood: 5, focus: 5, energy: 5, deepWork: 0,
      habits: {} 
    });
    setAiThinkingLogs([]);
    setDetectedTasks([]);
  };

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
      // Simple alert for now, replace with a proper toast component if available
      alert(msg);
  };

  // --- AI Logic ---
  const handleAIParse = async () => {
    const text = entry.note;
    if (!text) {
        showToast("❌ 請先輸入內容", "error");
        return;
    }

    setIsAiAnalyzing(true);
    setAiThinkingLogs(["Initializing text parser..."]);
    
    // 輔助延遲函數
    const wait = (ms: number) => new Promise(r => setTimeout(r, ms));

    try {
        await wait(600);
        setAiThinkingLogs(prev => [...prev, "Reading context..."]);
        
        // 1. 解析日期與基礎數據
        await wait(500);
        const mood = text.match(/(?:Mood|心情)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const focus = text.match(/(?:Focus|專注)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const energy = text.match(/(?:Energy|能量)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const deep = text.match(/(?:Deep|Reading|深度)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const dateMatch = text.match(/(?:Date|日期|^#\s*\[?)?\s*(\d{4}-\d{2}-\d{2})/m);
        
        setAiThinkingLogs(prev => [...prev, `Extracting Metrics: Mood=${mood?.[1]||'-'}, Focus=${focus?.[1]||'-'}`]);

        // 2. 解析圖譜種子
        await wait(600);
        const targetDate = dateMatch ? dateMatch[1] : entry.date;
        const graphMatch = text.match(/(?:Graph|Connections|關聯)(?:[\s:：]*)(?:[\r\n]+)([\s\S]*?)(?:$|^#)/mi);
        const graphContent = graphMatch ? graphMatch[1].trim() : '';
        const searchScope = graphContent || text;
        const seeds = CoreEngine.parseGraphSeeds(searchScope);
        const tags = seeds.tags.join(' ');
        const links = seeds.links.join(' ');
        
        if(tags) setAiThinkingLogs(prev => [...prev, `Identified Tags: ${tags}`]);
        if(links) setAiThinkingLogs(prev => [...prev, `Found Connections: ${links}`]);

        // 3. 習慣與任務偵測
        await wait(500);
        let detectedFocus = focus ? parseInt(focus[1]) : entry.focus;
        if (text.includes('URGENT') || text.includes('TODO')) {
            detectedFocus = Math.max(detectedFocus || 5, 8); 
            setAiThinkingLogs(prev => [...prev, "⚠️ Detected Priority Keywords. Boosting Focus."]);
        }

        let detectedHabits = { ...entry.habits };
        let habitCount = 0;
        config.habits.forEach(h => {
            if (text.toLowerCase().includes(h.id) || text.includes(h.label.split(' ')[0].toLowerCase())) {
                detectedHabits[h.id] = true;
                habitCount++;
            }
        });
        setAiThinkingLogs(prev => [...prev, `Matched ${habitCount} active habits`]);

        // 4. Task Bridge
        const tasks = CoreEngine.extractTasks(text);
        setDetectedTasks(tasks);
        if(tasks.length > 0) setAiThinkingLogs(prev => [...prev, `⚡ Extracted ${tasks.length} actionable tasks`]);

        // 5. 應用數據
        await wait(400);
        setAiThinkingLogs(prev => [...prev, "✅ Analysis Complete. Updating UI..."]);
        
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
        setAiThinkingLogs(prev => [...prev, `❌ Error: ${error.message}`]);
    } finally {
        setIsAiAnalyzing(false);
    }
  };


  // --- Render Components ---

  const renderAiTerminal = () => {
    if (!isAiAnalyzing && aiThinkingLogs.length === 0) return null;

    return (
        <div className="mb-4 bg-slate-900 rounded-xl p-4 border border-indigo-500/30 shadow-lg animate-fade-in">
            <div className="flex items-center gap-2 mb-2 border-b border-slate-800 pb-2">
                <Terminal size={14} className="text-emerald-400 animate-pulse"/>
                <span className="text-xs font-mono text-emerald-400 font-bold">AI_CORE_PROCESSOR</span>
            </div>
            <div className="font-mono text-xs space-y-1 h-32 overflow-y-auto custom-scrollbar flex flex-col-reverse">
                {/* 顯示最後一行游標 */}
                {isAiAnalyzing && <div className="text-emerald-500 animate-pulse">_</div>}
                {/* 顯示思考紀錄 */}
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
            
            {/* AI Terminal */}
            {renderAiTerminal()}

            {/* Manual Input Form Area (Replica of InputInterface logic but integrated) */}
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
                                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                                    {t}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className="flex justify-end gap-2 mt-4">
                    <button 
                        onClick={handleAIParse} 
                        disabled={isAiAnalyzing}
                        className={`px-4 py-2 rounded-xl bg-slate-700 text-indigo-300 text-xs font-bold hover:bg-slate-600 transition-colors flex items-center gap-2 border border-slate-600 ${isAiAnalyzing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <Cpu className={`w-3 h-3 ${isAiAnalyzing ? 'animate-pulse' : ''}`}/> 
                        {isAiAnalyzing ? "Analyzing..." : "AI Agent"}
                    </button>
                    <button onClick={() => handleSaveLog(null)} className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/30 flex items-center gap-2">
                        <Activity className="w-3 h-3"/> Save
                    </button>
                </div>
            </div>
            
             {/* Metrics Sliders */}
             <div className="bg-[#1e293b] p-6 rounded-3xl shadow-lg border border-slate-700 space-y-4 mt-4">
                {['mood', 'focus', 'energy'].map(k => (
                    <div key={k} className="flex items-center gap-4">
                        <label className="w-16 text-xs font-bold text-slate-400 uppercase">{k}</label>
                        <input 
                            type="range" min="0" max="10" 
                            value={entry[k]} 
                            onChange={e => setEntry({...entry, [k]: parseInt(e.target.value)})}
                            className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                        />
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
               <NeuralGraph logs={logs} onNodeClick={(node) => alert(`Clicked: ${node.label}`)} />
            </div>
            <div className="p-4 text-center text-slate-500 text-xs">
               <Activity className="w-3 h-3 inline mr-1"/> 
               目前共有 {logs.length} 個節點正在運作
            </div>
          </div>
        );

      case 'list':
        // --- 搜尋過濾邏輯 ---
        const filteredLogs = logs.filter(log => {
            const searchContent = (log.note + log.date).toLowerCase();
            return searchContent.includes(searchTerm.toLowerCase());
        }); // logs are already newest first typically, but if MOCK_LOGS is old->new, reverse it. MOCK_LOGS seems old->new.
        
        // Sort by date desc
        filteredLogs.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

        // --- 分頁計算邏輯 ---
        const totalPages = Math.ceil(filteredLogs.length / ITEMS_PER_PAGE);
        if (historyPage > totalPages && totalPages > 0) {
            setHistoryPage(1);
        }
        
        const startIndex = (historyPage - 1) * ITEMS_