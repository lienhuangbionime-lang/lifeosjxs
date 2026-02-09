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

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!text.trim() || isSubmitting) return;

    setIsSubmitting(true);

    try {
      // 1. Prepare data
      const selectedHabits = Object.keys(activeHabits).filter(id => activeHabits[id]);
      const habitLabels = selectedHabits
        .map(id => habits.find((h: Habit) => h.id === id)?.label)
        .filter(Boolean) as string[];

      // 2. Call backend API
      const { cortex } = await import('@/lib/api/client');
      const response = await cortex.ingest.submit({
        content: text,
        habits: habitLabels
      });

      // 2.5. Store analysis result
      if (response.data && response.data.markdown_body) {
        setAnalysis(response.data.markdown_body);
      }

      // 3. Show success toast
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);

      // 4. Reset form
      setText('');
      setActiveHabits({});

      // 5. Optionally notify parent (for local state update)
      if (onSave) {
        onSave({
          content: text,
          habits: activeHabits,
          date: new Date().toISOString()
        });
      }
    } catch (error: any) {
      console.error('🔥 Ingest API Error:', {
        message: error.message,
        url: '/api/py/ingest',
        timestamp: new Date().toISOString(),
        error: error
      });

      // Show user-friendly error
      const errorMsg = error.message?.includes('fetch') || error.message?.includes('Failed to fetch')
        ? 'Cannot connect to backend. Please check your internet connection.'
        : `Submission failed: ${error.message || 'Unknown error'}`;

      alert(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full p-6 pb-32 animate-fade-in relative max-w-3xl mx-auto w-full">
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

      {/* Cyberpunk Terminal Output */}
      <AnimatePresence>
        {analysis && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-8 overflow-hidden relative z-10"
          >
            <div className="bg-black/80 border border-neon-blue/30 rounded-2xl p-6 shadow-[0_0_20px_rgba(0,243,255,0.1)]">
              {/* Terminal Header */}
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-neon-blue/20">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/50" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                    <div className="w-3 h-3 rounded-full bg-green-500/50" />
                  </div>
                  <span className="text-neon-blue text-xs font-mono uppercase tracking-wider">
                    LifeOS v7.1 Analysis Terminal
                  </span>
                </div>
                <button
                  onClick={() => setAnalysis(null)}
                  className="p-1 hover:bg-white/5 rounded transition-colors"
                >
                  <X className="text-gray-500 hover:text-white" size={16} />
                </button>
              </div>

              {/* Terminal Content */}
              <div className="max-h-96 overflow-y-auto custom-scrollbar">
                <pre className="font-mono text-sm text-green-400 whitespace-pre-wrap leading-relaxed">
                  {analysis}
                </pre>
              </div>

              {/* Terminal Footer */}
              <div className="mt-4 pt-3 border-t border-neon-blue/20 flex justify-end">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(analysis);
                    setShowToast(true);
                    setTimeout(() => setShowToast(false), 2000);
                  }}
                  className="px-4 py-2 bg-neon-blue/10 hover:bg-neon-blue/20 border border-neon-blue/30 text-neon-blue rounded-lg transition-all text-xs font-mono uppercase tracking-wider"
                >
                  Copy to Clipboard
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
      <div className="flex justify-end items-center gap-4 relative z-10">
        <span className="text-xs text-slate-600 font-mono hidden sm:block">
          <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">⌘</span> + <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">Enter</span> to save
        </span>
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || isSubmitting}
          className="px-8 py-4 bg-white text-slate-900 rounded-2xl font-black text-sm hover:scale-105 active:scale-95 transition-all shadow-xl disabled:opacity-50 disabled:hover:scale-100 flex items-center gap-2"
        >
          {isSubmitting ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full"
              />
              PROCESSING...
            </>
          ) : (
            <>
              <Send size={18} /> INGEST
            </>
          )}
        </button>
      </div>

      {/* Success Toast */}
      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-8 right-8 bg-indigo-600 text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-3 z-50"
          >
            <CheckCircle size={24} className="text-green-300" />
            <span className="font-bold">Neural Capture Complete</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};