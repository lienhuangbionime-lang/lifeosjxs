'use client';

import React, { useState, useEffect } from 'react';
// ... (引入保持不變)
import { CaptureView } from '@/components/CaptureView';
import { GraphView } from '@/components/GraphView';
import { HistoryView } from '@/components/HistoryView';
import { SettingsView } from '@/components/SettingsView';
import { Dashboard } from '@/components/Dashboard';
import { ProjectBoard } from '@/components/ProjectBoard';
import { SystemStatus } from '@/components/SystemStatus'; // 記得引入這個

// MOCK DATA 保持不變...

export default function Home() {
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS); // 初始值先給 Mock，不要直接讀 localStorage
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list' | 'settings' | 'dashboard' | 'project'>('capture');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  // [關鍵修復] 定義掛載狀態
  const [isMounted, setIsMounted] = useState(false);

  // [關鍵修復] 1. 只有在掛載後 (Client-side) 才啟動
  useEffect(() => {
    setIsMounted(true);
    
    // 掛載後才去讀取 LocalStorage
    const saved = localStorage.getItem('life_os_logs_v8_0');
    if (saved) {
      try { setLogs(JSON.parse(saved)); } catch(e) { console.error(e); }
    }
  }, []);

  // 2. 自動存檔 (僅在掛載後)
  useEffect(() => {
    if (isMounted && logs !== MOCK_LOGS) {
      localStorage.setItem('life_os_logs_v8_0', JSON.stringify(logs));
    }
  }, [logs, isMounted]);

  // Handler 保持不變...
  const handleSaveLog = (newLog: any) => { setLogs(prev => [newLog, ...prev]); setActiveTab('graph'); };
  const handleImportLogs = (importedLogs: any[]) => { setLogs(prev => [...prev, ...importedLogs]); };

  // [關鍵修復] 3. 如果還沒掛載，顯示 Loading，確保前後端 HTML 一致
  if (!isMounted) {
    return (
      <div className="h-screen w-full bg-[#020617] flex flex-col items-center justify-center gap-4 text-slate-500">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="font-mono text-xs tracking-widest animate-pulse">INITIALIZING CORTEX...</span>
      </div>
    );
  }

  // --- 4. 以下為正式渲染 (Client Only) ---
  const bgClass = activeTab === 'graph' ? 'bg-[#0f172a] text-slate-200' : 'bg-[#020617] text-slate-200';
  
  // Menu Items 定義保持不變...
  const menuItems = [
    { id: 'capture', label: '日誌輸入', icon: PenTool }, // 需確認 PenTool 等圖示已引入
    // ... 其他 items
  ];

  return (
    // ... (原本的 JSX 結構保持不變)
    // 記得將 <SystemStatus /> 放入 Header
    // 記得移除 HistoryView 的 logs={logs} 屬性 (因為 V3 改自主讀取)
  );
}
手術部位 B：frontend-body/components/GraphView.tsx
請確保這裡使用了 dynamic import 來隔離 D3.js：
'use client';
import dynamic from 'next/dynamic';
// ... 其他引入

// [關鍵修復] 強制關閉 SSR
const NeuralGraph = dynamic(
  () => import('@/components/NeuralGraph').then((mod) => mod.NeuralGraph),
  { ssr: false } 
);

export const GraphView = ({ logs }: { logs?: any[] }) => {
  // ... (內容保持不變)
};