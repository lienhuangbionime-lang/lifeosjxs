// 檔案: frontend-body/app/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Menu, X, PenTool, Layers, List as ListIcon, Activity, Settings, LayoutTemplate } from 'lucide-react';
import { CaptureView } from '@/components/CaptureView';
import { GraphView } from '@/components/GraphView';
import { HistoryView } from '@/components/HistoryView';
import { SettingsView } from '@/components/SettingsView';
import { Dashboard } from '@/components/Dashboard';
import { ProjectBoard } from '@/components/ProjectBoard';

// --- MOCK DATA (預設資料) ---
const MOCK_LOGS = [
  { date: '2026-02-03', note: 'System initialized. Waiting for cortex connection...', metrics: { mood: 5, focus: 5 }, graphSeeds: { tags: ['system'], links: [] }, habits: {} },
];

export default function Home() {
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list' | 'settings' | 'dashboard' | 'project'>('capture');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  // [Fix 1] 防止 Hydration Error (水合錯誤) 的關鍵狀態
  const [isMounted, setIsMounted] = useState(false);

  // [Fix 2] 定義同步函式 (暫時只做簡單宣告，防止報錯)
  const syncMemories = async () => {
    try {
      // 這裡未來會呼叫 '/api/py/memories' 從 Railway 獲取資料
      console.log("📡 Connecting to Cortex...");
    } catch (e) {
      console.error("Sync failed:", e);
    }
  };

  useEffect(() => {
    setIsMounted(true); // 標記元件已掛載

    // A. 讀取瀏覽器快取 (V2 機制 - 速度快)
    const saved = localStorage.getItem('life_os_logs_v8_0');
    if (saved) {
      try { 
        setLogs(JSON.parse(saved)); 
      } catch(e) { console.error("Cache Error", e); }
    }
    
    // B. 啟動雲端同步 (V3 機制 - 資料真)
    syncMemories();
  }, []);

  // 當 logs 變動時，寫回快取 (備份機制)
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
    setLogs(prev => [...prev, ...importedLogs]);
  };

  // --- 4. 渲染 (Render) ---
  
  // [Fix 3] 如果還沒掛載，顯示 Loading 動畫，而不是 return null (白屏)
  if (!isMounted) {
    return (
      <div className="h-screen w-full bg-[#f8fafc] flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <div className="text-slate-400 font-mono text-xs tracking-widest animate-pulse">
          INITIALIZING LIFEOS v3.1...
        </div>
      </div>
    );
  }

  const bgClass = activeTab === 'graph' ? 'bg-[#0f172a] text-slate-200' : 'bg-[#f8fafc] text-slate-800';
  
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
      {/* Header */}
      <header className={`px-6 py-4 z-50 flex justify-between items-center border-b sticky top-0 backdrop-blur-sm ${activeTab === 'graph' ? 'border-slate-800 bg-[#0f172a]/90' : 'border-slate-200 bg-white/80'}`}>
        <h1 className={`text-lg font-black tracking-tight ${activeTab === 'graph' ? 'text-white' : 'text-slate-800'}`}>
          LifeOS <span className="text-indigo-500 text-xs align-top px-1">v3.1</span>
        </h1>
        <button 
          onClick={() => setIsMenuOpen(!isMenuOpen)} 
          className={`p-2 rounded-full transition-all ${activeTab === 'graph' ? 'hover:bg-slate-800 text-white' : 'hover:bg-slate-100 text-slate-600'}`}
        >
          {isMenuOpen ? <X size={20}/> : <Menu size={20}/>}
        </button>
      </header>

      {/* Dropdown Menu */}
      {isMenuOpen && (
        <div className="absolute top-16 right-4 z-[1] w-48 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 animate-scale-in origin-top-right">
          {menuItems.map((item) => (
            <button 
              key={item.id} 
              onClick={() => { setActiveTab(item.id as any); setIsMenuOpen(false); }}
              className={`w-full text-left px-4 py-3 flex items-center gap-3 text-sm font-bold transition-colors ${activeTab === item.id ? 'text-indigo-600 bg-indigo-50' : 'text-slate-600 hover:bg-slate-50'}`}
            >
              <item.icon size={16} />
              {item.label}
            </button>
          ))}
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-0 relative z-10 custom-scrollbar">
        {activeTab === 'capture' && <CaptureView onSave={handleSaveLog} />}
        {activeTab === 'graph' && <GraphView logs={logs} />}
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'project' && <ProjectBoard logs={logs} />}
        {activeTab === 'list' && <HistoryView logs={logs} />}
        {activeTab === 'settings' && <SettingsView logs={logs} onImport={handleImportLogs} />}
      </main>
    </div>
  );
}