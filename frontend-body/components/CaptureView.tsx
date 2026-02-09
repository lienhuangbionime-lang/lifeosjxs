'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, Image as ImageIcon, CheckCircle, Brain, X, Trash2 } from 'lucide-react';
import { CoreEngine } from '@/lib/ai/core';
import { useSettings, Habit } from '@/lib/hooks/useSettings';

interface CaptureViewProps {
  onSave: (entry: any) => void;
}

export const CaptureView = ({ onSave }: CaptureViewProps) => {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false); // Mock
  const { habits } = useSettings();

  // Local state for the current entry being crafted
  const [activeHabits, setActiveHabits] = useState<Record<string, boolean>>({});

  // Auto-detect habits based on text
  useEffect(() => {
    const detected: Record<string, boolean> = { ...activeHabits };
    let hasChange = false;

    habits.filter((h: Habit) => h.active).forEach((h: Habit) => {
      if (text.toLowerCase().includes(h.label.toLowerCase())) {
        if (!detected[h.id]) {
          detected[h.id] = true;
          hasChange = true;
        }
      }
    });

    if (hasChange) setActiveHabits(detected);
  }, [text, habits]);

  const handleSubmit = () => {
    if (!text.trim()) return;

    // 1. Process with Core Engine
    const content = CoreEngine.sanitizeLogEntry(text);

    const entry = {
      content,
      habits: activeHabits,
      date: new Date().toISOString()
    };

    // 2. Save
    onSave(entry);

    // 3. Reset
    setText('');
    setActiveHabits({});
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full p-6 animate-fade-in relative max-w-3xl mx-auto w-full">
      {/* --- Header --- */}
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white flex items-center gap-3">
          <Brain className="text-indigo-400 animate-pulse-slow" /> Neural Capture
        </h2>
        <p className="text-slate-500 font-mono text-sm mt-2">
          What is on your mind? <span className="text-indigo-500/50">#ideas #tasks #journal</span>
        </p>
      </div>

      {/* --- Input Area --- */}
      <div className="relative group mb-8 flex-1 min-h-[200px]">
        <textarea
          autoFocus
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Log your reality..."
          className="w-full h-full bg-[#0f172a] text-lg text-slate-200 placeholder:text-slate-600 p-6 rounded-3xl border border-slate-800 focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/10 transition-all resize-none outline-none custom-scrollbar leading-relaxed"
        />

        {/* Quick Actions */}
        <div className="absolute bottom-4 right-4 flex gap-2">
          <button
            onClick={() => setIsRecording(!isRecording)}
            className={`p-3 rounded-full transition-all ${isRecording ? 'bg-red-500/20 text-red-400 animate-pulse' : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'}`}
          >
            <Mic size={20} />
          </button>
          <button
            className="p-3 rounded-full bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-all"
          >
            <ImageIcon size={20} />
          </button>
        </div>
      </div>

      {/* --- Habit Selectors --- */}
      <div className="mb-8">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Context & Habits</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {habits.filter((h: Habit) => h.active).map((habit: Habit) => {
            const isActive = activeHabits[habit.id];
            // Try to find an icon, fallback to Circle
            const Icon = CoreEngine.getIconComponent(habit.icon) || CheckCircle;

            return (
              <button
                key={habit.id}
                onClick={() => setActiveHabits(prev => ({ ...prev, [habit.id]: !isActive }))}
                className={`p-3 rounded-xl border transition-all flex items-center gap-3 ${isActive ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'}`}
              >
                <Icon size={18} className={isActive ? 'text-white' : 'text-slate-500'} />
                <span className="text-xs font-bold">{habit.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* --- Submit --- */}
      <div className="flex justify-end items-center gap-4">
        <span className="text-xs text-slate-600 font-mono hidden sm:block">
          <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">⌘</span> + <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">Enter</span> to save
        </span>
        <button
          onClick={handleSubmit}
          disabled={!text.trim()}
          className="px-8 py-4 bg-white text-slate-900 rounded-2xl font-black text-sm hover:scale-105 active:scale-95 transition-all shadow-xl disabled:opacity-50 disabled:hover:scale-100 flex items-center gap-2"
        >
          <Send size={18} /> INGEST
        </button>
      </div>
    </div>
  );
};