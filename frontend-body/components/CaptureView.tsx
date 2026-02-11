'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, Image as ImageIcon, CheckCircle, Brain, X, Trash2, Save } from 'lucide-react';
import { CoreEngine } from '@/lib/ai/core';
import { useSettings, Habit } from '@/lib/hooks/useSettings';
import { cortex, EvolutionStatus } from '@/lib/api/client'; // Import cortex and EvolutionStatus

interface CaptureViewProps {
  onSave: (entry: any) => void;
}

export const CaptureView = ({ onSave }: CaptureViewProps) => {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false); // Mock
  const { habits } = useSettings();
  const [systemStatus, setSystemStatus] = useState<EvolutionStatus | null>(null); // State for system status

  // Fetch system status on mount
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await cortex.checkEvolution();
        setSystemStatus(status);
      } catch (e) {
        console.error("Failed to fetch system status", e);
      }
    };
    fetchStatus();
  }, []);

  // Local state for the current entry being crafted
  const [activeHabits, setActiveHabits] = useState<Record<string, boolean>>({});

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
        recognition.lang = 'zh-TW'; // Default to Traditional Chinese, maybe make configurable

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
          console.error("Speech error", event);
          setIsRecording(false);
        };

        recognition.start();
      } else {
        alert("Voice recognition not supported in this browser.");
        setIsRecording(false);
      }
    }
    return () => {
      if (recognition) recognition.stop();
    };
  }, [isRecording]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [detectedDate, setDetectedDate] = useState<string | null>(null); // [New] Store AI-detected date

  const handleSubmit = async (skipAi: boolean = false, mode: 'overwrite' | 'append' = 'append') => {
    if (!text.trim() || isSubmitting) return;

    setIsSubmitting(true);

    try {
      // 1. Prepare data
      const selectedHabits = Object.keys(activeHabits).filter(id => activeHabits[id]);
      const habitLabels = selectedHabits
        .map(id => habits.find((h: Habit) => h.id === id)?.label)
        .filter(Boolean) as string[];

      // 2. Call backend API
      // Always use ingest to save, but skipAi will bypass Gemini
      const response = await cortex.ingest.submit({
        content: text,
        habits: habitLabels,
        skipAi: skipAi, // [New] Pass skipAi flag
        mode: mode      // [New] Pass overwrite/append mode
      });

      // 2.5. Check Status
      if (response.status === 'failed') {
        throw new Error(response.message || 'Server failed to save entry');
      }

      // 2.6. Store analysis result
      if (response.data && response.data.markdown_body) {
        setAnalysis(response.data.markdown_body);
        // [New] Store detected date from AI meta
        if (response.data.meta?.date) {
          setDetectedDate(response.data.meta.date);
        }
      }

      // 3. Show success toast
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);

      // 4. Reset form ONLY if skipAi (SAVE button) - otherwise keep the input to show with analysis
      if (skipAi) {
        setText('');
        localStorage.removeItem('lifeos_capture_draft'); // Clear draft
        setActiveHabits({});
      }

      // 5. Optionally notify parent (for local state update)
      if (onSave) {
        // Construct a full LogEntry-like object for immediate UI update
        const newEntry = {
          date: response.data?.meta?.date || detectedDate || new Date().toLocaleDateString('en-CA'),
          content: response.data?.markdown_body || text, // Use analyzed markdown if available, else raw text
          mood: response.data?.meta?.metrics?.mood || 5,
          focus: response.data?.meta?.metrics?.focus || 5,
          energy: response.data?.meta?.metrics?.energy || 5,
          isAi: !skipAi,
          aiModel: skipAi ? "None" : response.model,
          // Merge raw inputs too just in case
          habits: activeHabits
        };
        onSave(newEntry);
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
      handleSubmit(false); // Default to Analyze on Ctrl+Enter
    }
  };

  const handleImageUpload = (file: File) => {
    if (!file) return;

    // 1. Convert image to Base64/DataURL for immediate preview/text integration
    // (In a production app, we would upload to Supabase Storage and get a URL)
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      // Insert markdown image syntax into text area
      const imageMarkdown = `\n![${file.name}](${result})\n`;
      setText(prev => prev + imageMarkdown);
      alert("Image added to log!");
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="flex flex-col h-full w-full pb-32 animate-fade-in relative overflow-y-auto custom-scrollbar">
      {/* --- Header --- */}
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white flex items-center gap-3">
          <Brain className="text-indigo-400 animate-pulse-slow" /> Neural Capture
        </h2>
        <p className="text-slate-500 font-mono text-sm mt-2 flex items-center justify-between">
          <span>What is on your mind? <span className="text-indigo-500/50">#ideas #tasks</span></span>
          <span className="text-[10px] bg-white/5 px-2 py-0.5 rounded border border-white/10 text-slate-400">
            Engine: {systemStatus ? `${systemStatus.model_versions?.[0]?.split('/').pop()} (Fast Mode)` : 'Loading...'}
          </span>
        </p>

      </div>

      {/* --- Input Area --- */}
      <div className="relative group mb-8 min-h-[200px]">
        <textarea
          autoFocus
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onDrop={(e) => {
            e.preventDefault();
            const file = e.dataTransfer.files?.[0];
            if (file && file.type.startsWith('image/')) {
              handleImageUpload(file);
            }
          }}
          onDragOver={(e) => e.preventDefault()}
          placeholder="Log your reality... (Drag & Drop images supported)"
          className="w-full h-full bg-[#0f172a] text-lg text-slate-200 placeholder:text-slate-600 p-6 rounded-3xl border border-slate-800 focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/10 transition-all resize-none outline-none custom-scrollbar leading-relaxed"
        />

        {/* Quick Actions */}
        <div className="absolute bottom-4 right-4 flex gap-2">
          <button
            onClick={() => {
              if (isRecording) {
                setIsRecording(false);
                // Stop logic handled by effect
              } else {
                setIsRecording(true);
                // Start logic handled by effect
              }
            }}
            className={`p-3 rounded-full transition-all ${isRecording ? 'bg-red-500/20 text-red-400 animate-pulse' : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'}`}
          >
            <Mic size={20} />
          </button>
          <input
            type="file"
            accept="image/*"
            className="hidden"
            id="image-upload"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleImageUpload(file);
            }}
          />
          <button
            onClick={() => document.getElementById('image-upload')?.click()}
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
            transition={{ duration: 0.3 }}
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
              <div className="overflow-y-auto custom-scrollbar">
                <pre className="font-mono text-sm text-green-400 whitespace-pre-wrap leading-relaxed">
                  {analysis}
                </pre>
              </div>

              {/* Terminal Footer */}
              <div className="mt-4 pt-3 border-t border-neon-blue/20 flex justify-between items-center bg-black/40 -mx-6 -mb-6 p-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setAnalysis(null);
                      setDetectedDate(null);
                      setText('');
                      localStorage.removeItem('lifeos_capture_draft');
                      setActiveHabits({});
                    }}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition-all text-xs font-bold"
                  >
                    DISCARD
                  </button>

                  <button
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(analysis);
                        setShowToast(true);
                        setTimeout(() => setShowToast(false), 2000);
                      } catch (e) {
                        alert("Clipboard Error: " + e);
                      }
                    }}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition-all text-xs font-bold"
                  >
                    COPY
                  </button>
                </div>

                <button
                  onClick={() => {
                    setAnalysis(null);
                    setDetectedDate(null);
                    setText('');
                    localStorage.removeItem('lifeos_capture_draft');
                    setActiveHabits({});
                    setShowToast(false);
                  }}
                  className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg transition-all text-xs font-bold uppercase tracking-wider flex items-center gap-2"
                >
                  <div className="flex items-center gap-2 text-green-400 font-bold text-xs uppercase tracking-wider mr-2">
                    <CheckCircle size={14} /> Saved
                  </div>
                  <span>Start New Entry</span>
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
      <div className="flex justify-end items-center gap-4 relative z-10 mb-8">

        {/* Quick Save Button */}
        <button
          onClick={async () => {
            // Basic Conflict Detection
            const today = new Date().toLocaleDateString('en-CA');
            // In a real app we'd fetch this, but for now we rely on the prompt or internal backend logic
            // Let's implement a simple user prompt if we think there's a conflict
            const choice = confirm("已有今日紀錄。點擊「確定」進行合併 (Merge)，點擊「取消」進行覆蓋 (Overwrite)。") ? 'append' : 'overwrite';
            handleSubmit(true, choice);
          }}
          disabled={!text.trim() || isSubmitting}
          className="px-6 py-4 bg-slate-800 text-slate-300 rounded-2xl font-bold text-sm hover:bg-slate-700 hover:text-white transition-all shadow-lg disabled:opacity-50 flex items-center gap-2"
        >
          <Save size={18} /> SAVE
        </button>

        {/* Ingest Button */}
        <button
          onClick={() => handleSubmit(false)}
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
              <Send size={18} /> INGEST & ANALYZE
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