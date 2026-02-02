'use client';

import React, { useState, useEffect } from 'react';
import { 
  Menu, X, PenTool, Layers, List as ListIcon, 
  Activity, Settings, LayoutTemplate, Cpu 
} from 'lucide-react';

// 引入您原有的組件 (器官)
import { CaptureView } from '@/components/CaptureView';
import { GraphView } from '@/components/GraphView';
import { HistoryView } from '@/components/HistoryView';
import { SettingsView } from '@/components/SettingsView'; // 這是 V0 新生成的
import { Dashboard } from '@/components/Dashboard';
import { ProjectBoard } from '@/components/ProjectBoard';

// 定義視圖類型
type ViewState = 'capture' | 'graph' | 'list' | 'settings' | 'dashboard' | 'project';

export default function Home() {
  // --- 1. 狀態管理 (V3.1 改用 Zustand，這裡僅保留 UI 狀態) ---
  const [activeTab, setActiveTab] = useState<ViewState>('capture');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  // 防禦性編程：防止 Hydration Error
  useEffect(() => setIsMounted(true), []);

  if (!isMounted) return null;

  // --- 2. 導航定義 (保留原本的功能) ---
  const menuItems = [
    { id: 'capture',   label: 'Capture Stream', icon: PenTool },
    { id: 'graph',     label: 'Neural Cortex',  icon: Layers },
    { id: 'dashboard', label: 'CCA Strategy',   icon: Activity },
    { id: 'project',   label: 'Project Board',  icon: LayoutTemplate },
    { id: 'list',      label: 'Memory Logs',    icon: ListIcon },
    { id: 'settings',  label: 'System Config',  icon: Settings },
  ];

  // --- 3. V3.1 渲染邏輯 ---
  return (
    // [Visual Mutation] 背景改為深色 Cyberpunk 風格
    <main className="min-h-screen bg-neutral-950 text-slate-200 font-sans relative overflow-hidden flex flex-col">
      
      {/* === 生物訊號背景 (The Matrix Grid) === */}
      <div className="fixed inset-0 bg-[linear-gradient(rgba(0,255,136,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,136,0.03)_1px,transparent_1px)] bg-[size:50px_50px] pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(0,0,0,0.8)_100%)] pointer-events-none" />

      {/* === 頂部導航欄 (Cortex Header) === */}
      <header className="px-6 py-4 z-50 flex justify-between items-center border-b border-white/10 backdrop-blur-md sticky top-0">
        <div className="flex items-center gap-2">
          {/* 加入脈衝動畫，象徵系統活著 */}
          <Cpu className="text-emerald-500 w-5 h-5 animate-pulse" />
          <h1 className="text-lg font-bold tracking-wider text-white">
            LIFE<span className="text-emerald-500">OS</span>
            <span className="text-xs ml-2 text-neutral-500 font-mono">v3.1 Autopoiesis</span>
          </h1>
        </div>
        
        {/* 選單按鈕 */}
        <button 
          onClick={() => setIsMenuOpen(!isMenuOpen)} 
          className={`p-2 rounded-full transition-colors z-50 ${isMenuOpen ? 'bg-white/10 text-white' : 'hover:bg-white/10 text-neutral-400'}`}
        >
          {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* === 下拉選單 (Neural Pathways) === */}
      {isMenuOpen && (
        <div className="absolute top-16 right-4 z-40 w-64 bg-neutral-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl p-2 animate-in fade-in slide-in-from-top-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id as ViewState);
                setIsMenuOpen(false);
              }}
              className={`w-full text-left px-4 py-3 flex items-center gap-3 text-sm font-medium rounded-lg transition-all ${
                activeTab === item.id 
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]' 
                  : 'text-neutral-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <item.icon size={16} />
              {item.label}
            </button>
          ))}
        </div>
      )}

      {/* === 主內容區 (Window Viewport) === */}
      <div className="flex-1 relative z-10 overflow-y-auto custom-scrollbar p-4 md:p-6">
        <div className="max-w-4xl mx-auto w-full h-full">
          
          {/* 
              CTO Note: 在 V3.1，我們不再透過 props 傳遞 logs。
              各個組件應自行透過 API Client 或 Store 獲取資料。
              這裡暫時傳入空物件或 dummy function 以防舊組件報錯。
          */}

          {activeTab === 'capture' && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
               <CaptureView onSave={() => { /* V3: 由組件內部呼叫 API */ }} /> 
            </div>
          )}

          {activeTab === 'graph' && (
            <div className="h-[600px] animate-in zoom-in-95 duration-500 bg-[#0b1120] rounded-2xl border border-white/10 overflow-hidden">
              <GraphView logs={[]} /> 
            </div>
          )}

          {activeTab === 'dashboard' && (
            <div className="animate-in fade-in duration-500">
              <Dashboard />
            </div>
          )}
          
          {activeTab === 'project' && (
            <div className="animate-in fade-in duration-500">
              <ProjectBoard logs={[]} />
            </div>
          )}

          {activeTab === 'list' && (
             <div className="animate-in fade-in duration-500">
               <HistoryView logs={[]} />
             </div>
          )}

          {activeTab === 'settings' && (
            <div className="animate-in fade-in duration-500">
              <SettingsView />
            </div>
          )}

        </div>
      </div>
    </main>
  );
}
