"use client";

import { useState, useEffect } from 'react';
import { CoreEngine } from '@/lib/ai/core';
import { NeuralGraph } from '@/components/NeuralGraph';
import { InputInterface } from '@/components/InputInterface';

export default function Home() {
    const [engine, setEngine] = useState<CoreEngine | null>(null);
    const [activeTab, setActiveTab] = useState<'graph' | 'input' | 'memory'>('input');
    const [isClient, setIsClient] = useState(false);

    useEffect(() => {
        setIsClient(true);
        const core = new CoreEngine();
        setEngine(core);
    }, []);

    if (!isClient || !engine) {
        return (
            <div className="flex items-center justify-center h-screen bg-[#0f172a] text-slate-400">
                Loading Neural Interface...
            </div>
        );
    }

    return (
        <div className="max-w-md mx-auto h-screen bg-[#0f172a] flex flex-col font-sans text-slate-200 relative shadow-2xl overflow-hidden">
            <header className="px-6 py-4 bg-[#0f172a]/90 backdrop-blur z-20 flex justify-between items-center border-b border-slate-800 sticky top-0">
                <h1 className="text-lg font-black tracking-tight text-white">LifeOS <span className="text-indigo-400 text-xs align-top border border-indigo-500/30 px-1 rounded">v2.0 Cloud</span></h1>
            </header>

            <main className="flex-1 overflow-hidden relative">
                {activeTab === 'graph' && (
                    <div className="absolute inset-0 z-0">
                    </div>
                )}
                
                {activeTab === 'input' && (
                    <div className="h-full overflow-y-auto pb-20 p-4">
                    </div>
                )}
            </main>

            <nav className="h-16 bg-[#0f172a] border-t border-slate-800 flex justify-around items-center z-30 shrink-0">
                <button 
                    onClick={() => setActiveTab('graph')}
                    className={`p-2 rounded-xl transition-all duration-300 ${activeTab === 'graph' ? 'text-indigo-400 bg-indigo-500/10' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
                </button>
                <button 
                    onClick={() => setActiveTab('input')}
                    className={`p-2 rounded-xl transition-all duration-300 ${activeTab === 'input' ? 'text-indigo-400 bg-indigo-500/10' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                </button>
            </nav>
        </div>
    );
}