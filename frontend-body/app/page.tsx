'use client';

import React, { useState, useEffect } from 'react';
import { Menu, X, PenTool, Layers, List as ListIcon, Activity, Settings, LayoutTemplate, Zap, Clock, TrendingUp, Quote, Trash2, Clipboard, Link as LinkIcon } from 'lucide-react';

// Components
import { CaptureView } from '@/components/CaptureView';
import { NeuralGraph } from '@/components/NeuralGraph';
import { HistoryView } from '@/components/HistoryView';
import { SettingsView } from '@/components/SettingsView';
import { Dashboard } from '@/components/Dashboard';
import { ProjectBoard } from '@/components/ProjectBoard';
import { SystemStatus } from '@/components/SystemStatus';
import { ConfirmModal, ContextModal } from '@/components/Modals';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';

// MOCK / DEFAULT DATA
const STORAGE_KEY_LOGS = 'life_os_logs_v10'; // Bumping version for new data structure if needed
const STORAGE_KEY_CONFIG = 'life_os_config_v10';
const STORAGE_KEY_CCA = 'life_os_cca_v10';

export default function Home() {
  // 1. State Definition
  const [logs, setLogs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list' | 'settings' | 'dashboard' | 'project'>('capture');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  // Modal States
  const [selectedEntry, setSelectedEntry] = useState<any>(null);
  const [contextNode, setContextNode] = useState<any>(null);
  const [confirmState, setConfirmState] = useState({ isOpen: false, title: '', message: '', action: null as any });

  // Other Data
  const [ccaData, setCcaData] = useState<any>({});

  // 2. Lifecycle: Init
  useEffect(() => {
    setIsMounted(true);

    // [Hybrid Strategy: Load Local First]
    const savedLogs = localStorage.getItem(STORAGE_KEY_LOGS);
    if (savedLogs) {
      try { setLogs(JSON.parse(savedLogs)); }
      catch (e) { console.error("Cache Error", e); }
    } else {
      // Fallback to minimal init?
    }

    const savedCCA = localStorage.getItem(STORAGE_KEY_CCA);
    if (savedCCA) {
      try { setCcaData(JSON.parse(savedCCA)); } catch (e) { }
    }

    // [Hybrid Strategy: Background Sync] could go here
    // fetch('/api/v1/sync')...
  }, []);

  // 3. Lifecycle: Auto-Save Local
  useEffect(() => {
    if (isMounted) {
      localStorage.setItem(STORAGE_KEY_LOGS, JSON.stringify(logs));
      localStorage.setItem(STORAGE_KEY_CCA, JSON.stringify(ccaData));
    }
  }, [logs, ccaData, isMounted]);

  // Handlers
  const handleSaveLog = (newLog: any) => {
    setLogs(prev => {
      // Remove existing if overwriting same date? Or append? 
      // Legacy behavior: Append or Overwrite based on date
      const filtered = prev.filter(l => l.date !== newLog.date);
      return [...filtered, newLog].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    });
    // setActiveTab('graph'); // Optional: switch to graph to see result immediately? Legacy behavior kept it on input.
    // Toast handled in CaptureView
  };

  const handleUpdateLogs = (newLogs: any[]) => {
    setLogs(newLogs);
  };

  const handleUpdateCCA = (month: string, field: string, value: string) => {
    setCcaData((prev: any) => ({ ...prev, [month]: { ...prev[month], [field]: value } }));
  };

  const requestDelete = (date: string) => {
    setConfirmState({
      isOpen: true,
      title: '刪除紀錄',
      message: `確定要刪除 ${date} 的紀錄嗎？`,
      action: () => {
        setLogs(prev => prev.filter(l => l.date !== date));
        setSelectedEntry(null);
        setConfirmState(prev => ({ ...prev, isOpen: false }));
      }
    });
  };

  // --- Render Helpers ---
  if (!isMounted) return <div className="h-screen bg-[#020617] flex items-center justify-center"><div className="w-6 h-6 border-2 border-indigo-500 rounded-full animate-spin"></div></div>;

  const bgClass = activeTab === 'graph' ? 'bg-[#0f172a] text-slate-200' : 'bg-[#f8fafc] text-slate-900';

  return (
    <div className={`max-w-md mx-auto h-screen flex flex-col font-sans relative shadow-2xl overflow-hidden transition-colors duration-500 ${bgClass}`}>

      {/* Modals */}
      <ConfirmModal
        isOpen={confirmState.isOpen}
        title={confirmState.title}
        message={confirmState.message}
        onConfirm={confirmState.action}
        onCancel={() => setConfirmState(prev => ({ ...prev, isOpen: false }))}
      />

      <ContextModal
        mainNode={contextNode}
        logs={logs}
        onClose={() => setContextNode(null)}
        onOpenEntry={setSelectedEntry}
      />

      {/* Entry Detail Viewer (Overlay) */}
      {selectedEntry && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in" onClick={() => setSelectedEntry(null)}>
          <div className="w-full max-w-lg max-h-[85vh] rounded-3xl shadow-2xl overflow-hidden flex flex-col animate-scale-in bg-white text-slate-900" onClick={e => e.stopPropagation()}>
            <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-white/95 backdrop-blur sticky top-0 z-10">
              <div className="flex flex-col">
                <h3 className="font-black text-2xl text-slate-800 tracking-tight">{selectedEntry.date}</h3>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  {selectedEntry.isStub ? 'Virtual Node' : new Date(selectedEntry.date).toLocaleDateString('en-US', { weekday: 'long', month: 'short' })}
                </span>
              </div>
              <div className="flex gap-2">
                <button onClick={() => { navigator.clipboard.writeText(selectedEntry.note) }} className="p-2 bg-slate-50 hover:bg-slate-100 rounded-full text-slate-400 transition-all"><Clipboard size={18} /></button>
                <button onClick={() => requestDelete(selectedEntry.date)} className="p-2 bg-red-50 hover:bg-red-100 text-red-500 rounded-full transition-all"><Trash2 size={18} /></button>
                <button onClick={() => setSelectedEntry(null)} className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-500 rounded-full transition-all"><X size={18} /></button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-0">
              <div className={`h-1.5 w-full ${selectedEntry.metrics.mood > 7 ? 'bg-gradient-to-r from-emerald-400 to-teal-500' : selectedEntry.metrics.mood < 4 ? 'bg-gradient-to-r from-rose-400 to-red-500' : 'bg-gradient-to-r from-indigo-400 to-purple-500'}`} />

              {selectedEntry.sections?.summary && (
                <div className="mx-5 mt-5 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                  <div className="flex items-center gap-2 mb-2 text-slate-400">
                    <Quote size={12} className="fill-current" />
                    <span className="text-[10px] font-bold uppercase tracking-widest">Day Summary</span>
                  </div>
                  <p className="text-sm font-medium text-slate-700 leading-relaxed italic">"{selectedEntry.sections.summary}"</p>
                </div>
              )}

              <div className="mx-5 mt-4 grid grid-cols-4 gap-2">
                {[
                  { l: 'Mood', v: selectedEntry.metrics.mood, c: 'indigo', i: Activity },
                  { l: 'Focus', v: selectedEntry.metrics.focus, c: 'rose', i: Zap },
                  { l: 'Energy', v: selectedEntry.metrics.energy, c: 'amber', i: TrendingUp },
                  { l: 'Deep', v: `${selectedEntry.metrics.deepWork}m`, c: 'blue', i: Clock },
                ].map(m => (
                  <div key={m.l} className={`bg-${m.c}-50 rounded-xl p-2 flex flex-col items-center justify-center border border-${m.c}-100`}>
                    <m.i size={12} className={`text-${m.c}-500 mb-1`} />
                    <span className={`text-lg font-black text-${m.c}-700`}>{m.v}</span>
                  </div>
                ))}
              </div>

              <div className="p-6">
                <MarkdownRenderer content={selectedEntry.note} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- Header --- */}
      <header className={`px-4 py-3 z-50 flex justify-between items-center border-b sticky top-0 backdrop-blur-md ${activeTab === 'graph' ? 'border-slate-800 bg-[#0f172a]/90' : 'border-slate-200 bg-white/90'}`}>
        <div className="flex items-center gap-3">
          <h1 className={`text-lg font-black tracking-tight ${activeTab === 'graph' ? 'text-white' : 'text-slate-900'}`}>
            LifeOS <span className="text-indigo-500 text-[10px] align-top">v10.3 Hybrid</span>
          </h1>
          <SystemStatus />
        </div>
        {/* Menu Button if needed, but we use Bottom Nav now */}
      </header>

      {/* --- Main Content --- */}
      <main className="flex-1 overflow-y-auto p-0 relative z-10 custom-scrollbar">
        {activeTab === 'capture' && <CaptureView onSave={handleSaveLog} />}
        {activeTab === 'graph' && (
          <div className="h-full flex flex-col p-4">
            <h3 className="text-white text-sm font-bold mb-2 flex items-center gap-2"><Activity size={16} className="text-emerald-400" /> Infinite Graph</h3>
            <NeuralGraph logs={logs} onNodeClick={setContextNode} />
          </div>
        )}
        {activeTab === 'dashboard' && <Dashboard logs={logs} ccaData={ccaData} onUpdateCCA={handleUpdateCCA} />}
        {activeTab === 'project' && <ProjectBoard logs={logs} onUpdateLogs={handleUpdateLogs} />}
        {activeTab === 'list' && <HistoryView logs={logs} onSelectEntry={setSelectedEntry} />}
        {activeTab === 'settings' && <SettingsView logs={logs} onImport={(l: any) => setLogs(prev => [...prev, ...l])} />}
      </main>

      {/* --- Bottom Nav --- */}
      <nav className={`${activeTab === 'graph' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border-t p-2 flex justify-around items-center z-30 pb-safe`}>
        {[
          { id: 'capture', icon: PenTool, label: 'Log' },
          { id: 'graph', icon: Layers, label: 'Graph' },
          { id: 'project', icon: LayoutTemplate, label: 'Board' },
          { id: 'dashboard', icon: Activity, label: 'Dash' },
          { id: 'list', icon: ListIcon, label: 'Foot' },
          { id: 'settings', icon: Settings, label: 'Sys' }
        ].map((tab: any) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all w-14 ${activeTab === tab.id ? 'text-indigo-500 bg-indigo-500/10' : (activeTab === 'graph' ? 'text-slate-500 hover:text-slate-300' : 'text-slate-400 hover:text-slate-600')}`}>
            <tab.icon size={20} className={activeTab === tab.id ? 'stroke-[2.5px]' : 'stroke-2'} />
            <span className="text-[9px] font-bold">{tab.label}</span>
          </button>
        ))}
      </nav>

    </div>
  );
}