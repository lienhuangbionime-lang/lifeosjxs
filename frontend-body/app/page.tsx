'use client';

import React, { useState, useEffect } from 'react';
import { Menu, X, PenTool, Layers, List as ListIcon, Activity, Settings, LayoutTemplate } from 'lucide-react';

// 引入各個視窗組件
import { CaptureView } from '@/components/CaptureView';
import { GraphView } from '@/components/GraphView';
import { HistoryView } from '@/components/HistoryView';
import { SettingsView } from '@/components/SettingsView';
import { Dashboard } from '@/components/Dashboard';
import { ProjectBoard } from '@/components/ProjectBoard';
// [Fix] 引入 SystemStatus 確保進化按鈕可用
import { SystemStatus } from '@/components/SystemStatus';

// --- MOCK DATA (預設資料) ---
const MOCK_LOGS = [
  { date: '2024-01-30', note: 'System Initialization...', metrics: { mood: 7, focus: 9 }, graphSeeds: { tags: ['system'], links: [] }, habits: {} },
];

export default function Home() {
  // 1. 狀態定義
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list' | 'settings' | 'dashboard' | 'project'>('capture');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  // [关键修复] 防止 Hydration Error 的掛載狀態
  const [isMounted, setIsMounted] = useState(false);

  // 2. 生命週期：初始化
  useEffect(() => {
    setIsMounted(true); // 標記為已掛載
    
    // 只有在客戶端才讀取 LocalStorage
    const saved = localStorage.getItem('life_os_logs_v8_0');
    if (saved) {
      try { 
        setLogs(JSON.parse(saved)); 
      } catch(e) { console.error("Cache Error", e); }
    }
  }, []);

  // 3. 生命週期：自動存檔
  useEffect(() => {
    if (isMounted && logs !== MOCK_LOGS) {
      localStorage.setItem('life_os_logs_v8_0', JSON.stringify(logs));
    }
  }, [logs, isMounted]);

  // Handler: 儲存日誌
  const handleSaveLog = (newLog: any) => {
    setLogs(prev => [newLog, ...prev]);
    setActiveTab('graph');
  };

  // Handler: 匯入日誌
  const handleImportLogs = (importedLogs: any[]) => {
    setLogs(prev => [...prev, ...importedLogs]);
  };

  // [CRITICAL FIX] 防止 Hydration Error
  // 在瀏覽器完成掛載前，顯示一個簡單的 Loading 畫面
  if (!isMounted) {
    return (
      <div className="h-screen w-full bg-[#020617] flex flex-col items-center justify-center gap-4 text-slate-500">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="font-mono text-xs tracking-widest animate-pulse">INITIALIZING CORTEX...</span>
      </div>
    );
  }

  // --- 4. 正式渲染 (Client Only) ---
  const bgClass = activeTab === 'graph' ? 'bg-[#0f172a] text-slate-200' : 'bg-[#020617] text-slate-200';
  
  const menuItems = [
    { id: 'capture', label: '日誌輸入', icon: PenTool },
    { id: 'graph', label: '神經網絡', icon: Layers },
    { id: 'dashboard', label: 'CCA 戰略', icon: Activity },
    { id: 'project', label: '專案戰情', icon: LayoutTemplate },
    { id: 'list', label: '歷史足跡', icon: ListIcon },
    { id: 'settings', label: '系統設定', icon: Settings },
  ];

  return (
    <div className={`max-w-md mx-auto h-screen flex flex-col font-sans relative shadow-2xl overflow-hidden transition-colors duration-500 ${bgClass}`}>
      
      {/* --- Header --- */}
      <header className={`px-4 py-3 z-50 flex justify-between items-center border-b sticky top-0 backdrop-blur-md ${activeTab === 'graph' ? 'border-slate-800 bg-[#0f172a]/90' : 'border-slate-800 bg-[#020617]/80'}`}>
        
        {/* Logo & System Status */}
        <div className="flex items-center gap-3">
            <h1 className={`text-lg font-black tracking-tight ${activeTab === 'graph' ? 'text-white' : 'text-slate-100'}`}>
            LifeOS <span className="text-indigo-500 text-[10px] align-top">v3.1</span>
            </h1>
            
            {/* 系統進化狀態指示器 */}
            <SystemStatus />
        </div>

        {/* Menu Button */}
        <button 
          onClick={() => setIsMenuOpen(!isMenuOpen)} 
          className={`p-2 rounded-full transition-all ${activeTab === 'graph' ? 'hover:bg-slate-800 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
        >
          {isMenuOpen ? <X size={20}/> : <Menu size={20}/>}
        </button>
      </header>

      {/* --- Dropdown Menu --- */}
      {isMenuOpen && (
        <div className="absolute top-16 right-4 z-50 w-48 bg-[#1e293b] rounded-2xl shadow-xl border border-slate-700 py-2 animate-scale-in origin-top-right">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id as any);
                setIsMenuOpen(false);
              }}
              className={`w-full text-left px-4 py-3 flex items-center gap-3 text-sm font-bold transition-colors ${
                activeTab === item.id 
                  ? 'text-indigo-400 bg-indigo-500/10' 
                  : 'text-slate-400 hover:bg-slate-800'
              }`}
            >
              <item.icon size={16} />
              {item.label}
            </button>
          ))}
        </div>
      )}

      {/* --- Main Content Area --- */}
      <main className="flex-1 overflow-y-auto p-0 relative z-10 custom-scrollbar">
        
        {/* 1. Capture */}
        {activeTab === 'capture' && <CaptureView onSave={handleSaveLog} />}
        
        {/* 2. Graph: 傳遞 logs 讓 D3 繪圖 */}
        {activeTab === 'graph' && <GraphView logs={logs} />}
        
        {/* 3. Dashboard */}
        {activeTab === 'dashboard' && <Dashboard />}
        
        {/* 4. Project */}
        {activeTab === 'project' && <ProjectBoard logs={logs} />}

        {/* 5. History: V3.1 版本自主讀取 API，移除 logs props */}
        {activeTab === 'list' && <HistoryView />}

        {/* 6. Settings */}
        {activeTab === 'settings' && <SettingsView logs={logs} onImport={handleImportLogs} />}
        
      </main>
    </div>
  );
}