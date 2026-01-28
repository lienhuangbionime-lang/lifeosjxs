"use client";
import React, { useState, useEffect } from 'react';
import { NeuralGraph } from '@/components/NeuralGraph';
import { InputInterface } from '@/components/InputInterface';
import { Activity, Network, Edit3, Settings } from 'lucide-react';

export default function LifeOS() {
    const [activeTab, setActiveTab] = useState('input');
    const [logs, setLogs] = useState([]); // 初始可以是空陣列，之後用 fetch 從 DB 抓

    // 模擬從 DB 獲取資料 (未來可換成 Server Component 或 SWR)
    useEffect(() => {
        // fetch('/api/logs').then(...) 
    }, []);

    const handleNewEntry = (data: any) => {
        // 暫時更新本地 State，實際資料已由 API 寫入 DB
        alert("資料已寫入雲端資料庫！");
    };

    return (
        <div className="max-w-md mx-auto h-screen bg-slate-50 flex flex-col font-sans text-slate-900 relative shadow-2xl overflow-hidden">
            <header className="px-6 py-4 bg-white/90 backdrop-blur z-20 flex justify-between items-center border-b border-slate-200/50 sticky top-0">
                <h1 className="text-lg font-black tracking-tight text-slate-900">LifeOS <span className="text-indigo-600 text-xs align-top">v2.0 Cloud</span></h1>
            </header>

            <main className="flex-1 overflow-y-auto p-4 scroll-smooth">
                {activeTab === 'input' && <InputInterface onSaveEntry={handleNewEntry} />}
                {activeTab === 'graph' && (
                    <div className="h-full flex flex-col">
                        <div className="bg-white p-4 rounded-3xl shadow-sm border border-slate-100 flex-1 flex flex-col">
                            <NeuralGraph logs={logs} onNodeClick={(node) => console.log(node)} />
                        </div>
                    </div>
                )}
                {/* 其他 Tab (Dashboard, History) 依此類推 */}
            </main>

            <nav className="bg-white border-t border-slate-200 p-2 flex justify-around items-center z-30 pb-safe">
                {[
                    {id:'input', icon:Edit3, label:'Log'},
                    {id:'graph', icon:Network, label:'Graph'},
                    {id:'settings', icon:Settings, label:'Sys'}
                ].map(tab => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all w-16 ${activeTab === tab.id ? 'text-indigo-600 bg-indigo-50' : 'text-slate-400 hover:bg-slate-50'}`}>
                        {React.createElement(tab.icon, { size: 20 })}
                        <span className="text-[10px] font-bold">{tab.label}</span>
                    </button>
                ))}
            </nav>
        </div>
    );
}
