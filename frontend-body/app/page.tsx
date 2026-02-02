'use client';

import React, { useState, useEffect } from 'react';
import { Menu, X, PenTool, Layers, Activity, Settings } from 'lucide-react';
// 暫時使用簡單的 Placeholder，因為原本的 components 可能也遺失了
// 我們先讓系統能跑起來，之後再把 components 補回來

export default function Home() {
  const [activeTab, setActiveTab] = useState('capture');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => { setIsMounted(true); }, []);

  if (!isMounted) return null;

  return (
    <div className="max-w-md mx-auto h-screen flex flex-col font-sans relative shadow-2xl bg-[#0f172a] text-slate-200">
      {/* Header */}
      <header className="px-6 py-4 z-50 flex justify-between items-center border-b border-slate-800 bg-[#0f172a]/90 backdrop-blur">
        <h1 className="text-lg font-black tracking-tight text-white">
          LifeOS <span className="text-indigo-500 text-xs align-top px-1">v3.1</span>
        </h1>
        <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="p-2 rounded-full hover:bg-slate-800 text-white transition-all">
          {isMenuOpen ? <X size={20}/> : <Menu size={20}/>}
        </button>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-6 relative z-10">
        <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-4">
          <Activity size={48} className="text-indigo-500 animate-pulse" />
          <p>LifeOS System Online</p>
          <div className="text-xs font-mono bg-slate-900 p-4 rounded-lg">
            Status: Body Reconstructed<br/>
            Cortex: Waiting for connection...
          </div>
        </div>
      </main>
    </div>
  );
}