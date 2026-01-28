'use client';

import React, { useState, useEffect } from 'react';
import { NeuralGraph } from '@/components/NeuralGraph';
import { InputInterface } from '@/components/InputInterface';
import { CoreEngine } from '@/lib/ai/core';
import { Layers, PenTool, List as ListIcon, Calendar, Activity } from 'lucide-react';

// 模擬初始資料 (避免空值導致黑畫面)
const MOCK_LOGS = [
  { date: '2024-01-28', note: 'Project LifeOS: Fix Vercel deploy #coding', metrics: { mood: 6, focus: 8, energy: 7 }, graphSeeds: { tags: ['coding', 'project'] } },
  { date: '2024-01-29', note: 'Family dinner at Taichung #life', metrics: { mood: 9, focus: 3, energy: 8 }, graphSeeds: { tags: ['life', 'family'] } }
];

export default function Home() {
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list'>('capture');

  // 處理新筆記儲存
  const handleSaveLog = (newLog: any) => {
    setLogs(prev => [newLog, ...prev]);
    setActiveTab('graph'); // 存完自動跳轉看圖
  };

  // 渲染主內容區
  const renderContent = () => {
    switch (activeTab) {
      case 'capture':
        return (
          <div className="h-full flex flex-col justify-center max-w-lg mx-auto w-full">
            <h2 className="text-2xl font-bold text-white mb-6 px-4 flex items-center gap-2">
               <PenTool className="text-indigo-400" /> Capture Flow
            </h2>
            <InputInterface onSaveEntry={handleSaveLog} />
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
        return (
          <div className="h-full overflow-y-auto pb-20 px-2 space-y-3">
            <h2 className="text-xl font-bold text-white mb-4 px-2 sticky top-0 bg-[#0f172a] py-2 z-10 flex items-center gap-2">
              <Calendar className="text-emerald-400"/> History Timeline
            </h2>
            {logs.map((log, idx) => (
              <div key={idx} className="bg-slate-800/50 p-4 rounded-xl border border-slate-700 hover:border-indigo-500/50 transition-colors">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-1 rounded">{log.date}</span>
                  <div className="flex gap-1">
                    {log.graphSeeds?.tags?.map((t:string) => (
                      <span key={t} className="text-[10px] bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded">#{t}</span>
                    ))}
                  </div>
                </div>
                <p className="text-slate-200 text-sm whitespace-pre-wrap">{log.note}</p>
                <div className="mt-3 flex gap-4 text-xs text-slate-500 font-mono">
                    <span>Mood: {log.metrics?.mood}</span>
                    <span>Focus: {log.metrics?.focus}</span>
                </div>
              </div>
            ))}
          </div>
        );
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#0f172a] text-slate-200 font-sans overflow-hidden">
      {/* Top Header */}
      <header className="px-6 py-3 bg-[#0f172a]/90 backdrop-blur z-20 border-b border-slate-800 flex justify-between items-center shrink-0">
        <h1 className="text-lg font-black tracking-tight text-white flex items-center gap-2">
          <Layers className="text-indigo-500"/> LifeOS <span className="text-indigo-400 text-[10px] border border-indigo-500/30 px-1 rounded align-top">BETA</span>
        </h1>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden relative p-4">
        {renderContent()}
      </main>

      {/* Bottom Navigation Bar */}
      <nav className="h-16 bg-[#1e293b] border-t border-slate-700 shrink-0 flex justify-around items-center px-2 pb-safe">
        <button 
          onClick={() => setActiveTab('capture')}
          className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all w-20 ${activeTab === 'capture' ? 'text-indigo-400 bg-slate-800' : 'text-slate-500 hover:text-slate-300'}`}
        >
          <PenTool size={20} />
          <span className="text-[10px] font-bold">Input</span>
        </button>

        <button 
          onClick={() => setActiveTab('graph')}
          className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all w-20 ${activeTab === 'graph' ? 'text-emerald-400 bg-slate-800' : 'text-slate-500 hover:text-slate-300'}`}
        >
          <Activity size={20} />
          <span className="text-[10px] font-bold">Graph</span>
        </button>

        <button 
          onClick={() => setActiveTab('list')}
          className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all w-20 ${activeTab === 'list' ? 'text-amber-400 bg-slate-800' : 'text-slate-500 hover:text-slate-300'}`}
        >
          <ListIcon size={20} />
          <span className="text-[10px] font-bold">Browse</span>
        </button>
      </nav>
    </div>
  );
}