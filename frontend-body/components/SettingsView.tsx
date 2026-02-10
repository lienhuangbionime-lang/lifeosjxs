'use client';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, Plus, RotateCcw, Save, Settings, CheckSquare, MessageSquare } from 'lucide-react';
import { useSettings } from '@/lib/hooks/useSettings';

interface SettingsProps {
  logs?: any[];
  onImport?: (logs: any[]) => void;
}

export const SettingsView = ({ logs, onImport }: SettingsProps) => {
  const { prompts, habits, apiKeys, addPrompt, removePrompt, addHabit, removeHabit, setApiKey, resetDefaults } = useSettings();

  // Local state for inputs
  const [newPrompt, setNewPrompt] = useState('');
  const [newHabit, setNewHabit] = useState('');

  // Helper (Legacy inline input - consider removing if fully moving to modal, but keeping for now)
  const APIInput = ({ label, skey, placeholder }: { label: string, skey: string, placeholder: string }) => (
    <div className="space-y-1">
      <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">{label}</label>
      <div className="relative">
        <input
          type="password"
          value={apiKeys[skey] || ''}
          onChange={(e) => setApiKey(skey, e.target.value)}
          placeholder={placeholder}
          className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:ring-1 focus:ring-pink-500/50 outline-none font-mono tracking-tighter"
        />
        <div className="absolute right-3 top-2.5 text-slate-600 pointer-events-none">
          <Save size={14} className={apiKeys[skey] ? "text-emerald-500" : ""} />
        </div>
      </div>
    </div>
  );

  // Handlers
  const handleAddPrompt = () => {
    if (newPrompt.trim()) {
      addPrompt(newPrompt.trim());
      setNewPrompt('');
    }
  };

  const handleAddHabit = () => {
    if (newHabit.trim()) {
      addHabit(newHabit.trim());
      setNewHabit('');
    }
  };

  return (
    <div className="p-6 pb-24 space-y-8 animate-fade-in text-slate-300">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-black text-white flex items-center gap-3">
            <Settings className="text-indigo-400 animate-spin-slow" /> System Settings
          </h2>
          <p className="text-slate-500 text-sm mt-1">Configure your Neural Operating System.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { if (confirm('Reset to defaults?')) resetDefaults(); }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 text-xs font-bold transition-colors"
          >
            <RotateCcw size={12} /> Reset System
          </button>
        </div>
      </div>

      {/* ... Prompts and Habits ... */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* 1. Daily Prompts */}
        <section className="bg-neutral-800/50 backdrop-blur-md rounded-3xl p-6 border border-white/5 shadow-xl">
          {/* ... existing code ... */}
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <MessageSquare className="text-emerald-400" size={20} /> Daily Prompts
          </h3>
          <div className="space-y-3 mb-4 max-h-[300px] overflow-y-auto custom-scrollbar pr-2">
            <AnimatePresence>
              {prompts.map((p: string, idx: number) => (
                <motion.div
                  key={`${p}-${idx}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                  className="group flex justify-between items-center bg-neutral-900/80 p-3 rounded-xl border border-white/5 hover:border-emerald-500/30 transition-colors"
                >
                  <span className="text-sm text-slate-300 font-medium">{p}</span>
                  <button
                    onClick={() => removePrompt(idx)}
                    className="text-slate-600 hover:text-red-400 p-1.5 rounded-lg hover:bg-white/5 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={14} />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          <div className="flex gap-2 relative">
            <input
              value={newPrompt}
              onChange={e => setNewPrompt(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAddPrompt()}
              placeholder="Add a new reflection question..."
              className="flex-1 bg-neutral-900 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:ring-2 focus:ring-emerald-500/50 outline-none placeholder:text-slate-600"
            />
            <button onClick={handleAddPrompt} className="bg-emerald-500 hover:bg-emerald-400 text-emerald-950 p-2.5 rounded-xl transition-colors font-bold"><Plus size={18} /></button>
          </div>
        </section>

        {/* 2. Habit Tracker */}
        <section className="bg-neutral-800/50 backdrop-blur-md rounded-3xl p-6 border border-white/5 shadow-xl">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <CheckSquare className="text-indigo-400" size={20} /> Habit Tracker
          </h3>
          <div className="space-y-3 mb-4 max-h-[300px] overflow-y-auto custom-scrollbar pr-2">
            <AnimatePresence>
              {habits.map((h: any, idx: number) => (
                <motion.div
                  key={`${h.id}-${idx}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                  className="group flex justify-between items-center bg-neutral-900/80 p-3 rounded-xl border border-white/5 hover:border-indigo-500/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xs">
                      {h.label.slice(0, 1)}
                    </div>
                    <span className="text-sm text-slate-300 font-bold">{h.label}</span>
                  </div>
                  <button onClick={() => removeHabit(idx)} className="text-slate-600 hover:text-red-400 p-1.5 rounded-lg hover:bg-white/5 transition-colors opacity-0 group-hover:opacity-100"><Trash2 size={14} /></button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          <div className="flex gap-2 relative">
            <input
              value={newHabit}
              onChange={e => setNewHabit(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAddHabit()}
              placeholder="Add a new habit..."
              className="flex-1 bg-neutral-900 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500/50 outline-none placeholder:text-slate-600"
            />
            <button onClick={handleAddHabit} className="bg-indigo-500 hover:bg-indigo-400 text-white p-2.5 rounded-xl transition-colors font-bold"><Plus size={18} /></button>
          </div>
        </section>

        {/* 3. API Connections (Full Width) */}
        <section className="lg:col-span-2 bg-neutral-800/50 backdrop-blur-md rounded-3xl p-6 border border-white/5 shadow-xl">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Settings className="text-pink-500" size={20} /> API Connections
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <APIInput label="Google Gemini API Key" skey="google_api_key" placeholder="AIza..." />
            <APIInput label="Supabase URL" skey="supabase_url" placeholder="https://..." />
            <APIInput label="Supabase Key" skey="supabase_key" placeholder="eyJ..." />
          </div>
        </section>
      </div>

      <div className="flex items-center justify-center pt-8 opacity-50">
        <span className="text-[10px] font-mono tracking-widest text-slate-600">SYSTEM CONFIGURATION V3.1 // PERSISTENCE ACTIVE</span>
      </div>
    </div>
  );
};