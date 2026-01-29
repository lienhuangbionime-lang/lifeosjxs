// 檔案位置: app/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
    Layers, PenTool, List as ListIcon, Activity, 
    Settings, Upload 
} from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';
import { CaptureView } from '@/components/CaptureView';
import { GraphView } from '@/components/GraphView';
import { HistoryView } from '@/components/HistoryView';
import { SettingsView } from '@/components/SettingsView'; // [New]

// --- MOCK DATA ---
const MOCK_LOGS = [
  { date: '2024-01-28', note: 'Project LifeOS: Fix Vercel deploy #coding', metrics: { mood: 6, focus: 8, energy: 7, deepWork: 4 }, graphSeeds: { tags: ['coding', 'project'], links: [] }, habits: { h4: true }, isSignal: false },
  { date: '2024-01-29', note: 'Family dinner at Taichung #life', metrics: { mood: 9, focus: 3, energy: 8, deepWork: 0 }, graphSeeds: { tags: ['life', 'family'], links: [] }, habits: {}, isSignal: false },
  { date: '2024-01-30', note: 'Deep work session on AI core logic #coding - [ ] Refactor core.ts', metrics: { mood: 7, focus: 9, energy: 6, deepWork: 6 }, graphSeeds: { tags: ['coding', 'ai'], links: [] }, habits: { h1: true, h4: true }, isSignal: true },
];

export default function Home() {
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list' | 'settings'>('capture');
  
  // Hydration Fix
  useEffect(() => {
      const saved = localStorage.getItem('life_os_logs_v8_0');
      if (saved) {
          try { setLogs(JSON.parse(saved)); } catch(e) { console.error(e); }
      }
  }, []);

  // Auto-Save
  useEffect(() => {
      if (logs !== MOCK_LOGS) {
          localStorage.setItem('life_os_logs_v8_0', JSON.stringify(logs));
      }
  }, [logs]);

  const handleSaveLog = (newLog: any) => {
      setLogs(prev => [newLog, ...prev]);
      setActiveTab('graph');
  };

  const handleImportLogs = (importedLogs: any[]) => {
      setLogs(prev => {
          const existingDates = new Set(prev.map(l => l.date));
          const filteredNew = importedLogs.filter(l => !existingDates.has(l.date));
          const merged = [...prev, ...filteredNew].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
          return merged;
      });
  };

  return (
    <div className="max-w-md mx-auto h-screen bg-[#0f172a] flex flex-col font-sans text-slate-200 relative shadow-2xl overflow-hidden">
        <header className="px-6 py-4 bg-[#0f172a]/90 backdrop-blur z-20 flex justify-between items-center border-b border-slate-800 sticky top-0">
            <h1 className="text-lg font-black tracking-tight text-white">LifeOS <span className="text-indigo-400 text-xs align-top border border-indigo-500/30 px-1 rounded">v2.0 Cloud</span></h1>
            <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center"><span className="text-xs font-bold text-indigo-300">LH</span></div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 relative z-10 custom-scrollbar">
            {activeTab === 'capture' && <CaptureView onSave={handleSaveLog} />}
            {activeTab === 'graph' && <GraphView logs={logs} />}
            {activeTab === 'list' && <HistoryView logs={logs} />}
            {activeTab === 'settings' && <SettingsView logs={logs} onImport={handleImportLogs} />}
        </main>

        <nav className="absolute bottom-6 left-6 right-6 h-16 bg-[#1e293b]/90 backdrop-blur-md rounded-2xl border border-slate-700/50 shadow-2xl flex justify-around items-center px-2 z-50">
            <button onClick={() => setActiveTab('capture')} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all ${activeTab === 'capture' ? 'text-indigo-400 bg-indigo-500/10 scale-105' : 'text-slate-500 hover:text-slate-300'}`}><PenTool size={20} strokeWidth={activeTab === 'capture' ? 2.5 : 2} /><span className="text-[10px] font-bold">Capture</span></button>
            <button onClick={() => setActiveTab('graph')} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all ${activeTab === 'graph' ? 'text-indigo-400 bg-indigo-500/10 scale-105' : 'text-slate-500 hover:text-slate-300'}`}><Layers size={20} strokeWidth={activeTab === 'graph' ? 2.5 : 2} /><span className="text-[10px] font-bold">Neural</span></button>
            <button onClick={() => setActiveTab('list')} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all ${activeTab === 'list' ? 'text-indigo-400 bg-indigo-500/10 scale-105' : 'text-slate-500 hover:text-slate-300'}`}><ListIcon size={20} strokeWidth={activeTab === 'list' ? 2.5 : 2} /><span className="text-[10px] font-bold">History</span></button>
            <button onClick={() => setActiveTab('settings')} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all ${activeTab === 'settings' ? 'text-indigo-400 bg-indigo-500/10 scale-105' : 'text-slate-500 hover:text-slate-300'}`}><Settings size={20} strokeWidth={activeTab === 'settings' ? 2.5 : 2} /><span className="text-[10px] font-bold">Sys</span></button>
        </nav>
    </div>
  );
}