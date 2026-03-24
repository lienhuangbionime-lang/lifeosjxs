'use client';
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, Activity, Zap, Shield, RefreshCcw } from 'lucide-react';

interface BrainContext {
  active_focus: string;
  last_updated: string;
  status?: string;
}

export const BrainStateView = () => {
  const [context, setContext] = useState<BrainContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchContext = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/v1/brain/context');
      if (res.ok) {
        const data = await res.json();
        setContext(data);
      }
    } catch (e) {
      console.error("Failed to fetch brain context", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchContext();
    const interval = setInterval(fetchContext, 30000); // Polling every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 bg-slate-900/50 backdrop-blur-xl border border-indigo-500/20 rounded-2xl">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
            <Brain className="w-6 h-6 text-indigo-400 animate-pulse" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Core Brain State</h2>
            <p className="text-xs text-indigo-400 font-mono uppercase tracking-widest">Sovereign Active Memory v4.7</p>
          </div>
        </div>
        <button onClick={fetchContext} className="p-2 hover:bg-white/5 rounded-full transition-colors">
          <RefreshCcw className="w-4 h-4 text-slate-400" />
        </button>
      </div>

      <div className="space-y-6">
        {/* Active Focus Card */}
        <div className="p-4 bg-indigo-500/5 border border-indigo-500/10 rounded-xl">
          <div className="flex items-center gap-2 mb-2 text-indigo-300">
            <Activity className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-wider">Current Focus</span>
          </div>
          <p className="text-lg text-white font-medium leading-relaxed">
            {isLoading ? "Synchronizing..." : context?.active_focus || "Awaiting Commander Signal..."}
          </p>
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className={`p-4 border rounded-xl transition-all ${
            context?.status && context.status !== 'IDLE' 
              ? 'bg-rose-500/10 border-rose-500/20' 
              : 'bg-emerald-500/5 border-emerald-500/10'
          }`}>
            <div className={`flex items-center gap-2 mb-1 ${
              context?.status && context.status !== 'IDLE' ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              <Zap className={`w-3 h-3 ${context?.status && context.status !== 'IDLE' ? 'animate-bounce' : ''}`} />
              <span className="text-[10px] font-bold uppercase tracking-wider">Brain Pulse Status</span>
            </div>
            <p className="text-sm text-white font-mono uppercase tracking-tighter">
              {isLoading ? "POLLING..." : context?.status || "CONNECTED"}
            </p>
          </div>
          <div className="p-4 bg-amber-500/5 border border-amber-500/10 rounded-xl">
            <div className="flex items-center gap-2 mb-1 text-amber-400">
              <Shield className="w-3 h-3" />
              <span className="text-[10px] font-bold uppercase tracking-wider">Soul Integrity</span>
            </div>
            <p className="text-sm text-white font-mono">100% SECURE</p>
          </div>
        </div>

        {/* Historical Continuity */}
        <div className="pt-4 border-t border-white/5">
          <p className="text-[10px] text-slate-500 font-mono text-center">
            LAST SYNCED: {context?.last_updated ? new Date(context.last_updated).toLocaleString() : "NEVER"}
          </p>
        </div>
      </div>
    </div>
  );
};
