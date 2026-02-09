'use client';

import React, { useState, useEffect } from 'react';
import { Edit3, ListIcon as ListTodo, Copy, ExternalLink, GitMerge, Hash, Link as LinkIcon, Cpu, Save, BookOpen, Terminal, Zap, Activity, Brain, Star } from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';

// Helper for clipboard
const copyToClipboard = async (text: string) => {
  if (!text) return false;
  try { await navigator.clipboard.writeText(text); return true; } catch (err) { return false; }
};

interface CaptureViewProps {
  onSave: (log: any) => void;
}

export const CaptureView = ({ onSave }: CaptureViewProps) => {
  // Local state for form
  const [entry, setEntry] = useState({
    date: new Date().toISOString().split('T')[0],
    mood: 5, focus: 5, energy: 5, readingTime: 0,
    habits: {} as Record<string, boolean>,
    note: '',
    graphSeeds: { tags: '', links: '', content: '' }
  });

  const [notification, setNotification] = useState<{ msg: string, type: string } | null>(null);
  const [detectedTasks, setDetectedTasks] = useState<string[]>([]); // [Task Bridge] State

  // Init Logic to ensure date is set
  useEffect(() => {
    if (!entry.date) setEntry(prev => ({ ...prev, date: new Date().toISOString().split('T')[0] }));
  }, []);

  const showToast = (msg: string, type = 'success') => { setNotification({ msg, type }); setTimeout(() => setNotification(null), 3000); };

  // [AI Agent] Enhanced Regex Logic & Task Extraction
  const handleAIParse = () => {
    const text = entry.note;
    if (!text) return;

    const mood = text.match(/(?:Mood|心情)[\s\S]*?(\d+(?:\.\d+)?)/i);
    const focus = text.match(/(?:Focus|專注)[\s\S]*?(\d+(?:\.\d+)?)/i);
    const energy = text.match(/(?:Energy|能量)[\s\S]*?(\d+(?:\.\d+)?)/i);
    const deep = text.match(/(?:Deep|Reading|深度)[\s\S]*?(\d+(?:\.\d+)?)/i);

    const dateMatch = text.match(/(?:Date|日期|^#\s*\[?)?\s*(\d{4}-\d{2}-\d{2})/m);
    const targetDate = dateMatch ? dateMatch[1] : entry.date;

    const graphMatch = text.match(/(?:Graph|Connections|關聯)(?:[\s:：]*)(?:[\r\n]+)([\s\S]*?)(?:$|^#)/mi);
    const graphContent = graphMatch ? graphMatch[1].trim() : '';

    const searchScope = graphContent || text;
    const tags = (searchScope.match(/#([\w\u4e00-\u9fa5]+)/g) || []).join(' ');
    const links = (searchScope.match(/\[\[(.*?)\]\]/g) || []).join(' ');

    let detectedFocus = focus ? parseInt(focus[1]) : entry.focus;
    if (text.includes('URGENT') || text.includes('TODO')) {
      detectedFocus = Math.max(detectedFocus || 5, 8);
    }

    let detectedHabits = { ...entry.habits };
    DEFAULT_HABITS.forEach(h => {
      if (text.toLowerCase().includes(h.id) || text.includes(h.label.split(' ')[0])) {
        detectedHabits[h.id] = true;
      }
    });

    // [Task Bridge] Extract tasks
    const tasks = CoreEngine.extractTasks(text);
    setDetectedTasks(tasks);

    setEntry(prev => ({
      ...prev,
      date: targetDate,
      mood: mood ? parseInt(mood[1]) : prev.mood,
      focus: detectedFocus,
      energy: energy ? parseInt(energy[1]) : prev.energy,
      readingTime: deep ? parseInt(deep[1]) : prev.readingTime,
      habits: detectedHabits,
      graphSeeds: { tags: tags, links: links, content: graphContent }
    }));
    showToast(`🪄 AI 分析完成 (提取 ${tasks.length} 個待辦)`);
  };

  const handleSaveEntry = async () => {
    const finalSeeds = {
      tags: entry.graphSeeds?.tags || '',
      links: entry.graphSeeds?.links || '',
      content: entry.graphSeeds?.content || ''
    };

    let finalNote = entry.note;
    if (!finalNote) {
      finalNote = `# [${entry.date}] Log\n> Mood: ${entry.mood} | Focus: ${entry.focus}\n\n## Summary\n${entry.graphSeeds?.tags ? `Tags: ${entry.graphSeeds.tags}` : ''}`;
    }

    // Core Weakness Warning
    if ((entry.habits['creation'] || entry.habits['native_coding']) && entry.readingTime < 15 && !finalNote.includes('Core Weakness')) {
      finalNote += "\n\n⚠️ [Warning: Core Weakness]";
      showToast("⚠️ 偵測到核心能力虛弱", "warning");
    }

    // Construct Logic Object
    const newEntry = {
      ...entry,
      metrics: { mood: entry.mood, focus: entry.focus, energy: entry.energy, deepWork: entry.readingTime },
      graphSeeds: finalSeeds,
      note: finalNote,
      timestamp: Date.now()
    };

    // 1. Pass to parent (App level state) - Optimistic update
    onSave(newEntry);

    // 2. [Backend Sync] 
    try {
      // Background sync - do not await blocking UI
      fetch('/api/v1/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: finalNote,
          date: entry.date,
          metrics: newEntry.metrics,
          habits: newEntry.habits
        })
      }).then(res => {
        if (!res.ok) console.error("Backend Sync Failed");
        else console.log("Backend Synced");
      });
    } catch (e) { console.error("Sync Error", e); }

    showToast("✅ 紀錄已寫入 (Neural Sync)");
    setDetectedTasks([]); // Clear tasks after save
    // Reset entry (except date stays same or advances?) 
    // Keeping date allows rapid multiple entry for same day
  };

  return (
    <div className="space-y-6 pb-24 animate-fade-in relative">
      {notification && (
        <div className={`fixed top-6 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-full text-xs font-bold shadow-xl z-[100] flex items-center gap-2 animate-fade-in-up ${notification.type === 'error' ? 'bg-red-500 text-white' : 'bg-slate-800 text-white'}`}>
          {notification.msg}
        </div>
      )}

      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
        <div className="flex justify-between items-center mb-4">
          <span className="text-sm font-bold text-slate-600 flex items-center gap-2"><Edit3 className="w-4 h-4" /> DAILY LOG</span>
          <input type="date" value={entry.date} onChange={e => setEntry({ ...entry, date: e.target.value })} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1 text-sm font-mono outline-none" />
        </div>
        <textarea
          value={entry.note} onChange={e => setEntry({ ...entry, note: e.target.value })}
          placeholder="# [YYYY-MM-DD] Title\n> Mood: 8 | Focus: 7\n[T:30] (S) Task...\n\n## Graph\n#ProjectA [[2024-01-01]]"
          className="w-full h-40 p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-100 outline-none resize-none leading-relaxed"
        />

        {/* [Task Bridge] UI Section */}
        {detectedTasks.length > 0 && (
          <div className="mt-4 bg-blue-50 border border-blue-100 rounded-xl p-3 animate-fade-in">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-blue-600 flex items-center gap-1"><ListTodo size={12} /> AI Task Bridge</span>
              <div className="flex gap-2">
                <button onClick={() => { copyToClipboard(detectedTasks.join('\n')); showToast("Tasks Copied!"); }} className="text-[10px] bg-white px-2 py-1 rounded border border-blue-200 text-blue-600 hover:bg-blue-100 flex items-center gap-1"><Copy size={10} /> Copy All</button>
                <a href="https://tasks.google.com/embed/?origin=https://mail.google.com" target="_blank" rel="noopener noreferrer" className="text-[10px] bg-blue-600 px-2 py-1 rounded text-white hover:bg-blue-700 flex items-center gap-1"><ExternalLink size={10} /> Open GTasks</a>
              </div>
            </div>
            <ul className="space-y-1">
              {detectedTasks.map((t, i) => (
                <li key={i} className="text-xs text-blue-800 flex items-start gap-2">
                  <span className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0"></span>
                  {t}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-col gap-3">
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 mb-2 text-slate-400 text-xs font-bold uppercase tracking-wider"><GitMerge size={12} /> Graph Context</div>
            <textarea
              placeholder="Paste your ## Graph section here or let AI parse it..."
              value={entry.graphSeeds?.content || ''}
              onChange={e => setEntry({ ...entry, graphSeeds: { ...entry.graphSeeds, content: e.target.value } })}
              className="bg-transparent w-full text-xs font-mono outline-none text-slate-700 placeholder:text-slate-300 resize-none h-16"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-indigo-50 p-2 rounded-xl flex items-center gap-2 border border-indigo-100">
              <Hash className="w-4 h-4 text-indigo-400" />
              <input placeholder="Tags" value={entry.graphSeeds?.tags || ''} onChange={e => setEntry({ ...entry, graphSeeds: { ...entry.graphSeeds, tags: e.target.value } })} className="bg-transparent w-full text-xs font-mono outline-none text-indigo-800 placeholder:text-indigo-300" />
            </div>
            <div className="bg-indigo-50 p-2 rounded-xl flex items-center gap-2 border border-indigo-100">
              <LinkIcon className="w-4 h-4 text-indigo-400" />
              <input placeholder="Links" value={entry.graphSeeds?.links || ''} onChange={e => setEntry({ ...entry, graphSeeds: { ...entry.graphSeeds, links: e.target.value } })} className="bg-transparent w-full text-xs font-mono outline-none text-indigo-800 placeholder:text-indigo-300" />
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={handleAIParse} className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 transition-colors flex items-center gap-2"><Cpu className="w-3 h-3" /> AI Agent</button>
          <button onClick={handleSaveEntry} className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200 flex items-center gap-2"><Save className="w-3 h-3" /> Save</button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-4">
        {[{ k: 'mood', c: 'indigo', l: 'Mood' }, { k: 'focus', c: 'rose', l: 'Focus' }, { k: 'energy', c: 'amber', l: 'Energy' }, { k: 'readingTime', c: 'blue', l: 'Deep Work', m: 240, s: 10 }].map(m => (
          <div key={m.k} className="flex items-center gap-4">
            <label className="w-20 text-xs font-bold text-slate-400 uppercase">{m.l}</label>
            <input type="range" min="0" max={m.m || 10} step={m.s || 1} value={(entry as any)[m.k]} onChange={e => setEntry({ ...entry, [m.k]: parseInt(e.target.value) })} className={`flex-1 h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-${m.c}-500`} />
            <span className={`w-8 text-right text-sm font-black text-${m.c}-500`}>{(entry as any)[m.k]}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3">
        {DEFAULT_HABITS.map(habit => {
          const Icon = CoreEngine.getIconComponent(habit.icon);
          const isActive = entry.habits[habit.id];
          return (
            <button key={habit.id} onClick={() => setEntry({ ...entry, habits: { ...entry.habits, [habit.id]: !isActive } })}
              className={`p-4 rounded-2xl border transition-all flex items-center justify-between ${isActive ? 'bg-slate-800 border-slate-800 text-white shadow-lg' : 'bg-white border-slate-100 text-slate-400'}`}>
              <span className="text-xs font-bold">{habit.label}</span><Icon className={`w-5 h-5 ${isActive ? 'opacity-100' : 'opacity-20'}`} />
            </button>
          );
        })}
      </div>
    </div>
  );
};