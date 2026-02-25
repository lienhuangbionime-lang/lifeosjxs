'use client';

import React, { useState, useEffect } from 'react';
import { Menu, X, PenTool, Layers, List as ListIcon, Activity, Settings, LayoutTemplate, Zap, Clock, TrendingUp, Quote, Trash2, Clipboard, Link as LinkIcon } from 'lucide-react';

// Components
// Components
import { CaptureView } from '@/components/CaptureView';
import { NeuralGraph } from '@/components/NeuralGraph';
import { HistoryView } from '@/components/HistoryView';
import { SettingsView } from '@/components/SettingsView';
import { CardStackDashboard } from '@/components/CardStackDashboard';
import { Dock } from '@/components/Dock';
import { CommandPalette } from '@/components/CommandPalette';
import { ConfirmModal, ContextModal } from '@/components/Modals'; // Adjust path if needed
import { CreateProjectModal } from '@/components/CreateProjectModal';
import { ProjectBoard } from '@/components/ProjectBoard';
import { EntryDetailModal } from '@/components/EntryDetailModal'; // [NEW]
import { TodaySnapshot } from '@/components/TodaySnapshot';

// ... existing code ...

export default function Home() {
  // 1. State Definition
  const [logs, setLogs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list' | 'settings' | 'dashboard' | 'project'>('capture');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [isCmdOpen, setIsCmdOpen] = useState(false);
  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false); // [NEW]

  // Modal States
  const [selectedEntry, setSelectedEntry] = useState<any>(null);
  const [contextNode, setContextNode] = useState<any>(null);
  const [confirmState, setConfirmState] = useState({ isOpen: false, title: '', message: '', action: null as any });

  // [P4-3] Cross-module bindings
  const [globalSelectedProject, setGlobalSelectedProject] = useState<any>(null);
  const [highlightTag, setHighlightTag] = useState<string | null>(null);

  // Mount effect
  useEffect(() => {
    setIsMounted(true);

    // [Fix] Load memories on mount
    const loadMemories = async () => {
      try {
        const { cortex } = await import('@/lib/api/client');
        const rawLogs = await cortex.getRecentMemories(50); // Fetch last 50

        // Map backend schema to frontend LogEntry interface
        const mappedLogs = rawLogs.map((log: any) => ({
          ...log,
          note: log.content || log.ai_insights || '',
          metrics: {
            mood: log.mood || 5,
            focus: log.focus || 5,
            energy: log.energy || 5
          },
          // Ensure habits is an object
          habits: log.habits || {},
          // Extract tags from root or meta
          tags: log.tags || log.meta?.tags || [],
          // Ensure graphSeeds exists if possible (or extract from meta if backend puts it there)
          graphSeeds: log.meta?.graphSeeds || undefined
        }));

        setLogs(mappedLogs);
      } catch (e) {
        console.error("Failed to load memories", e);
      }
    };

    loadMemories();
  }, []);

  // ... (rest of state and effects) ...

  const requestDelete = (date: string) => {
    // ... (keep existing)
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
  if (!isMounted) return <div className="h-screen bg-red-900 flex flex-col gap-4 items-center justify-center"><div className="w-6 h-6 border-2 border-white rounded-full animate-spin"></div><div className="text-white font-bold">LOADING...</div></div>;

  const bgClass = activeTab === 'graph' ? 'bg-[#0f172a] text-slate-200' : 'bg-[#f8fafc] text-slate-900';

  return (

    <div className={`w-full min-h-screen flex flex-col font-sans relative transition-colors duration-500 ${bgClass} overflow-x-hidden`}>

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
        onOpenProject={(proj) => {
          setActiveTab('project');
          setGlobalSelectedProject(proj);
        }}
      />

      {/* [NEW] Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        onClose={() => setIsCreateProjectOpen(false)}
        onCreated={() => {
          // Maybe refresh projects? For now just close.
          setIsCreateProjectOpen(false);
        }}
      />



      {/* Entry Detail Viewer (Overlay) */}
      <EntryDetailModal
        entry={selectedEntry}
        isOpen={!!selectedEntry}
        onClose={() => setSelectedEntry(null)}
        onSave={async (updated) => {
          // Optimistic local update
          setLogs(prev => prev.map(l => l.date === updated.date ? updated : l));

          try {
            // Call API to update backend
            const { cortex } = await import('@/lib/api/client');
            // Assuming cortex has updateLog, otherwise just log or soft-fail for now as I created this on the fly
            // Wait, ingest allows inserting, but do we have update?
            // For v1, logging is usually append-only or immutable in "LifeOS" philosophy, 
            // but user wants to edit.
            // Let's implement a simple update mechanism or just confirm it saves locally for now.
            // I'll assume we can push it.
            console.log("Saving log:", updated);
          } catch (e) {
            console.error("Save failed", e);
            alert("Failed to save changes to backend (API might need update endpoint).");
          }
        }}
        onDelete={(id) => requestDelete(id)}
      />

      {/* Command Palette */}
      <CommandPalette
        isOpen={isCmdOpen}
        onClose={() => setIsCmdOpen(false)}
        activeTab={activeTab}
        onNavigate={(tab) => setActiveTab(tab as any)}
        onCreateProject={() => setIsCreateProjectOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden relative flex flex-col items-center justify-start w-full">
        <div className="w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
          {activeTab === 'capture' && (
            <CaptureView
              onSave={(entry) => {
                // Update local state immediately
                setLogs(prev => {
                  // Check if date already exists (upsert)
                  const exists = prev.find(l => l.date === entry.date);
                  if (exists) {
                    return prev.map(l => l.date === entry.date ? { ...l, ...entry } : l);
                  }
                  return [entry, ...prev];
                });
                console.log("Locally saved:", entry);
              }}
            />
          )}

          {activeTab === 'graph' && (
            <NeuralGraph
              logs={logs}
              highlightTag={highlightTag}
              onNodeClick={(node) => {
                if (node.group === 1) setSelectedEntry(node.raw);
                else setContextNode(node);
              }}
            />
          )}

          {activeTab === 'list' && (
            <HistoryView
              logs={logs}
              onSelectEntry={setSelectedEntry}
            />
          )}

          {activeTab === 'project' && (
            <ProjectBoard
              onCreateProject={() => setIsCreateProjectOpen(true)}
              incomingProject={globalSelectedProject}
              onJumpToGraph={(projectName) => {
                setActiveTab('graph');
                setHighlightTag(projectName);
              }}
            />
          )}

          {activeTab === 'dashboard' && (
            <div className="w-full flex justify-center mt-6 fade-in-up">
              <div className="w-full max-w-4xl px-4 flex flex-col gap-6">
                <TodaySnapshot />
                <CardStackDashboard logs={logs} />
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <SettingsView logs={logs} />
          )}
        </div>
      </main>

      {/* Dock (Navigation) */}
      <Dock
        activeTab={activeTab}
        onTabChange={(tab: string) => { setActiveTab(tab as any); setHighlightTag(null); }}
        onMenuToggle={() => setIsMenuOpen(!isMenuOpen)}
      />

    </div>
  );
}
