"use client";
import React, { useState, useEffect } from 'react';
import { NeuralGraph } from '@/components/NeuralGraph'; // 指向 components/NeuralGraph.tsx
import { InputInterface } from '@/components/InputInterface';
import { Activity, Network, Edit3, Settings } from 'lucide-react';
import { CoreEngine } from '@/lib/ai/core';

export default function LifeOS() {
    const [activeTab, setActiveTab] = useState('input');
    const [logs, setLogs] = useState<any[]>([]);

    // 模擬從資料庫載入 (實際上你可以用 fetch('/api/logs') 或是 Prisma Server Component)
    // 這裡為了讓前端先跑起來，我們用 localStorage 做快取
    useEffect(() => {
        const saved = localStorage.getItem('life_os_logs_v8_0');
        if (saved) setLogs(JSON.parse(saved));
    }, []);

    const handleSaveEntry = (newEntry: any) => {
        // Optimistic Update (前端先顯示)
        const processed = CoreEngine.sanitizeLogEntry(newEntry);
        const newLogs = [...logs.filter(l => l.date !== processed.date), processed];
        
        setLogs(newLogs.sort((a,b) => new Date(a.date).getTime() - new Date(b.date).getTime()));
        localStorage.setItem('life_os_logs_v8_0', JSON.stringify(newLogs));
    };

    return (
        <div className="max-w-md mx-auto h-screen bg-[#0f172a] flex flex-col font-sans text-slate-200 relative shadow-2xl overflow-hidden">
            <header className="px-6 py-4 bg-[#0f172a]/90 backdrop-blur z-20 flex justify-between items-center border-b border-slate-800 sticky top-0">
                <h1 className="text-lg font-black tracking-tight text-white">LifeOS <span className="text-indigo-400 text-xs align-top border border-indigo-500/30 px-1 rounded">v2.0 Cloud</span></h1>
            </header>

            <main className="flex-1 overflow-y-auto p-4 scroll-smooth custom-scrollbar">
                {activeTab === 'input' && <InpcoreutInterface onSaveEntry={handleSaveEntry} />}
                {activeTab === 'graph' && (
                    <div className="h-full flex flex-col">
                        <div className="bg-[#1e293b] p-1 rounded-3xl shadow-sm border border-slate-700 flex-1 flex flex-col">
                            <NeuralGraph logs={logs} onNodeClick={(n) => alert(`Clicked: ${n.id}`)} />
                        </div>
                    </div>
                )}
                {/* 其他 Tab 暫位符 */}
                {activeTab === 'dashboard' && <div className="text-center text-slate-500 mt-20">Dashboard Loading...</div>}
            </main>

            <nav className="bg-[#1e293b] border-t border-slate-800 p-2 flex justify-around items-center z-30 pb-safe">
                {[
                    {id:'input', icon:Edit3, label:'Log'},
                    {id:'graph', icon:Network, label:'Graph'},
                    {id:'dashboard', icon:Activity, label:'Dash'},
                    {id:'settings', icon:Settings, label:'Sys'}
                ].map(tab => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all w-16 ${activeTab === tab.id ? 'text-indigo-400 bg-indigo-500/10' : 'text-slate-500 hover:bg-slate-800'}`}>
                        {React.createElement(tab.icon, { size: 20 })}
                        <span className="text-[10px] font-bold">{tab.label}</span>
                    </button>
                ))}
            </nav>
        </div>
    );
}
