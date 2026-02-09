'use client';

import React from 'react';
import { Activity, Zap, TrendingUp, Clock, AlertTriangle } from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';

interface HistoryViewProps {
  logs?: any[];
  onSelectEntry?: (log: any) => void;
}

export const HistoryView = ({ logs = [], onSelectEntry }: HistoryViewProps) => {
  const historyLogs = [...logs].reverse();

  // Fallback if onSelectEntry is not provided (though it should be)
  const handleSelect = (log: any) => {
    if (onSelectEntry) onSelectEntry(log);
  };

  const getPreviewText = (text: string) => {
    if (!text) return '無詳細內容';
    return CoreEngine.extractInsight(text);
  };

  return (
    <div className="space-y-4 pb-24 animate-fade-in px-4 pt-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-base font-bold text-slate-700 px-1">近期足跡 ({historyLogs.length})</h3>
      </div>
      {historyLogs.map((log) => {
        const insight = CoreEngine.extractInsight(log.note);
        // Current CoreEngine returns string, so no 'type' property. 
        // We can check if it contains "Alert" or similar if we really want, but for now disable drift.
        const isDrift = false;
        const m = log.metrics?.mood ?? 5;
        const moodColor = m >= 8 ? 'bg-emerald-400' : m <= 3 ? 'bg-red-400' : 'bg-indigo-400';

        // Active Habits (using DEFAULT_HABITS for icons logic if needed)
        const activeHabits = Object.keys(log.habits || {}).filter(h => log.habits[h]);

        return (
          <div
            key={log.date}
            onClick={() => handleSelect(log)}
            className={`group p-5 rounded-3xl border relative cursor-pointer hover:shadow-lg transition-all bg-white border-slate-100 overflow-hidden`}
          >
            {/* Visual DNA Border */}
            <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${moodColor}`} />

            <div className="flex justify-between items-start mb-3 pl-3">
              <div className="flex flex-col">
                <span className="text-xl font-black text-slate-800 font-mono tracking-tight">{log.date}</span>
                <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">
                  {new Date(log.date).toLocaleDateString('en-US', { weekday: 'long' })}
                </span>
              </div>

              <div className="flex flex-col items-end gap-1">
                <div className="flex gap-1">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 bg-indigo-50 text-indigo-600`}>
                    <Activity size={10} /> {m}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 bg-rose-50 text-rose-600">
                    <Zap size={10} /> {log.metrics?.focus}
                  </span>
                </div>
                <div className="flex gap-1">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 bg-amber-50 text-amber-600">
                    <TrendingUp size={10} /> {log.metrics?.energy}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 bg-blue-50 text-blue-600">
                    <Clock size={10} /> {log.metrics?.deepWork}
                  </span>
                </div>
              </div>
            </div>

            <div className="text-sm text-slate-600 font-sans leading-relaxed line-clamp-2 mb-3 pl-3 pr-1">
              {log.sections?.summary || getPreviewText(log.note)}
            </div>

            <div className="pl-3 flex flex-col gap-2">
              {isDrift && (
                <div className="p-2 bg-slate-900 text-white rounded-lg text-xs font-mono flex items-center gap-2 shadow-sm w-fit">
                  <AlertTriangle size={12} className="text-amber-400" />
                  <span className="truncate max-w-[200px]">{insight}</span>
                </div>
              )}
              {activeHabits.length > 0 && (
                <div className="flex gap-2 mt-1">
                  {activeHabits.map(h => {
                    const habitConfig = DEFAULT_HABITS.find(ch => ch.id === h);
                    if (!habitConfig) return null;
                    const Icon = CoreEngine.getIconComponent(habitConfig.icon);
                    return <div key={h} className="text-slate-400 bg-slate-50 p-1 rounded-md"><Icon size={12} /></div>
                  })}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};