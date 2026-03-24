'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, Image as ImageIcon, CheckCircle, Brain, X, Trash2, Save, Sparkles, Loader2 } from 'lucide-react';
import { CoreEngine } from '@/lib/ai/core';
import { useSettings, Habit } from '@/lib/hooks/useSettings';
import { cortex } from '@/lib/api/client';

import { BrainStateView } from './BrainStateView';

interface CaptureViewProps {
  onSave: (entry: any) => void;
}

export const CaptureView = ({ onSave }: CaptureViewProps) => {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const { habits } = useSettings();

  const [contextualPrompts, setContextualPrompts] = useState<string[]>([]);
  const [isLoadingPrompts, setIsLoadingPrompts] = useState(true);

  // Fetch contextual prompts on mount
  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        setIsLoadingPrompts(true);
        const data = await cortex.brain.getContextualPrompts();
        if (data && data.prompts) {
          setContextualPrompts(data.prompts);
        }
      } catch (e) {
        console.error("Failed to fetch contextual prompts", e);
      } finally {
        setIsLoadingPrompts(false);
      }
    };
    fetchPrompts();
  }, []);

  // [New] Auto-Draft: Load from LocalStorage on mount
  useEffect(() => {
    const savedDraft = localStorage.getItem('lifeos_capture_draft');
    if (savedDraft) {
      setText(savedDraft);
    }
  }, []);

  // [New] Auto-Draft: Save to LocalStorage on change
  useEffect(() => {
    localStorage.setItem('lifeos_capture_draft', text);
  }, [text]);

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

  // Voice Recognition
  useEffect(() => {
    let recognition: any;
    if (isRecording) {
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        // @ts-ignore
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'zh-TW';

        recognition.onresult = (event: any) => {
          let finalTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            }
          }
          if (finalTranscript) {
            setText(prev => prev + (prev ? ' ' : '') + finalTranscript);
          }
        };

        recognition.onerror = (event: any) => {
          setIsRecording(false);
        };

        recognition.start();
      } else {
        alert("Voice recognition not supported.");
        setIsRecording(false);
      }
    }
    return () => {
      if (recognition) recognition.stop();
    };
  }, [isRecording]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMsg, setToastMsg] = useState('Neural Capture Complete');
  const [analysis, setAnalysis] = useState<string | null>(null);

  const handleSubmit = async (skipAi: boolean = false, mode: 'overwrite' | 'append' = 'append') => {
    if (!text.trim() || isSubmitting) return;
    setIsSubmitting(true);

    try {
      const selectedHabits = Object.keys(activeHabits).filter(id => activeHabits[id]);
      const habitLabels = selectedHabits
        .map(id => habits.find((h: Habit) => h.id === id)?.label)
        .filter(Boolean) as string[];

      const response = await cortex.ingest.submit({
        content: text,
        habits: habitLabels,
        skipAi: skipAi,
        mode: mode,
        source: "capture"
      });

      if (response.status === 'failed') throw new Error(response.message || 'Save failed');

      if (response.data && response.data.markdown_body) {
        setAnalysis(response.data.markdown_body);
      }

      setToastMsg((response.link_result?.completed_tasks ?? 0) > 0 ? `✅ Completed ${response.link_result?.completed_tasks} tasks` : 'Neural Capture Complete');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);

      if (skipAi) {
        setText('');
        localStorage.removeItem('lifeos_capture_draft');
        setActiveHabits({});
      }

      if (onSave) {
        onSave({
          date: response.data?.meta?.date || new Date().toLocaleDateString('en-CA'),
          content: response.data?.markdown_body || text,
          isAi: !skipAi
        });
      }
    } catch (error: any) {
      alert(`Submission failed: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      if (file.type.startsWith('image/')) {
        setText(prev => prev + `\n![${file.name}](${result})\n`);
      } else {
        setText(prev => prev + `\n--- [Attachment: ${file.name}] ---\n` + result + '\n---\n');
      }
    };
    if (file.type.startsWith('image/') || file.type === 'application/pdf') {
      reader.readAsDataURL(file);
    } else {
      reader.readAsText(file);
    }
  };

  return (
    <div className="flex flex-col h-full w-full pb-32 animate-fade-in relative overflow-y-auto custom-scrollbar">
      
      {/* 1. Sovereign Channels (Tags) */}
      <div className="flex flex-wrap gap-2 mb-6 mt-2">
        {[
          { tag: '#SOUL', color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20', label: '審美偏執' },
          { tag: '#FRICTION', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', label: '主權摩擦' },
          { tag: '#BODY', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', label: '身體記憶' },
          { tag: '#GREEN', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', label: '綠燈前進' },
          { tag: '#SPARK', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20', label: '非邏輯閃光' },
          { tag: '#EVO', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', label: '系統演化' }
        ].map((item) => (
          <button
            key={item.tag}
            onClick={() => setText(prev => prev.includes(item.tag) ? prev.replace(item.tag, '').trim() : `${prev} ${item.tag}`.trim())}
            className={`px-4 py-2 rounded-xl border text-xs font-black transition-all active:scale-90 flex items-center gap-2 ${text.includes(item.tag) ? `${item.bg} ${item.border} ${item.color} shadow-lg shadow-black/50` : 'bg-slate-900 border-slate-800 text-slate-500 hover:border-slate-700'}`}
          >
            <span className={item.color}>{item.tag}</span>
            <span className="opacity-50 font-medium">{item.label}</span>
          </button>
        ))}
      </div>

      {/* 2. Contextual Prompts */}
      {!isLoadingPrompts && contextualPrompts.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {[
            "現在身體哪裡感到最緊繃？",
            "這個卡點，能不能縮小成 10 分鐘的微實驗？",
            "今天有什麼地方觸碰到了你的審美底線？"
          ].map((p, idx) => (
            <button
              key={`sov-${idx}`}
              onClick={() => setText(prev => prev ? prev + '\n' + p : p)}
              className="px-4 py-1.5 text-sm bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/20 rounded-full transition-all"
            >
              🎯 {p}
            </button>
          ))}
          {contextualPrompts.slice(0, 1).map((p, i) => (
            <button
              key={i}
              onClick={() => setText(prev => prev ? prev + '\n' + p : p)}
              className="px-4 py-1.5 text-sm bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 rounded-full transition-all"
            >
              ✨ {p}
            </button>
          ))}
        </div>
      )}

      {/* 3. Input Area */}
      <div className="relative group mb-8 min-h-[250px]">
        <textarea
          autoFocus
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Capture a spark of sovereignty..."
          className="w-full h-full min-h-[250px] bg-[#020617] text-xl text-slate-100 placeholder:text-slate-700 p-8 rounded-[30px] border-2 border-slate-900 focus:border-indigo-500/40 focus:ring-8 focus:ring-indigo-500/5 transition-all resize-none outline-none custom-scrollbar leading-relaxed"
        />

        <div className="absolute bottom-6 right-6 flex gap-3">
          <button
            onClick={() => setIsRecording(!isRecording)}
            className={`p-4 rounded-2xl transition-all ${isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
          >
            <Mic size={24} />
          </button>
          <input type="file" className="hidden" id="file-upload" onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])} />
          <button
            onClick={() => document.getElementById('file-upload')?.click()}
            className="p-4 rounded-2xl bg-slate-800 text-slate-400 hover:text-white transition-all"
          >
            <ImageIcon size={24} />
          </button>
        </div>
      </div>

      {/* 4. Analysis Output (Terminal) */}
      <AnimatePresence>
        {analysis && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }} className="mb-8">
            <div className="bg-[#020617] border-2 border-indigo-500/20 rounded-3xl p-6 relative">
              <button onClick={() => setAnalysis(null)} className="absolute top-4 right-4 text-slate-600 hover:text-white">
                <X size={20} />
              </button>
              <pre className="whitespace-pre-wrap font-mono text-sm text-indigo-100/90 max-h-[400px] overflow-y-auto">
                {analysis}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 5. Habits */}
      <div className="mb-8">
        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-3">Context & Habits</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {habits.filter(h => h.active).map(h => {
             const isActive = activeHabits[h.id];
             const Icon = CoreEngine.getIconComponent(h.icon) || CheckCircle;
             return (
               <button
                 key={h.id}
                 onClick={() => setActiveHabits(prev => ({ ...prev, [h.id]: !isActive }))}
                 className={`p-3 rounded-xl border transition-all flex items-center gap-3 ${isActive ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'}`}
               >
                 <Icon size={16} />
                 <span className="text-[11px] font-bold uppercase">{h.label}</span>
               </button>
             );
          })}
        </div>
      </div>

      {/* 6. Footer Actions */}
      <div className="flex justify-end gap-4 mb-8">
        <button
          onClick={() => handleSubmit(true)}
          disabled={!text.trim() || isSubmitting}
          className="px-6 py-4 bg-slate-800 text-slate-300 rounded-2xl font-bold text-sm hover:bg-slate-700 hover:text-white transition-all shadow-lg disabled:opacity-50 flex items-center gap-2"
        >
          <Save size={18} /> SAVE
        </button>
        <button
          onClick={() => handleSubmit(false)}
          disabled={!text.trim() || isSubmitting}
          className="px-8 py-4 bg-indigo-600 text-white rounded-2xl font-black text-sm hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/20 flex items-center gap-2 uppercase tracking-wider"
        >
          {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />} ANALYZE & INGEST
        </button>
      </div>

      {showToast && (
        <motion.div initial={{ y: 50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="fixed bottom-32 left-1/2 -translate-x-1/2 bg-emerald-600 text-white px-6 py-3 rounded-full font-bold shadow-2xl z-50">
          {toastMsg}
        </motion.div>
      )}
    </div>
  );
};