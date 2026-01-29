// 檔案位置: components/HistoryView.tsx
'use client';

import React, { useState } from 'react';
import { List as ListIcon, Filter, Zap, TrendingUp, Clock, ArrowRight, Activity } from 'lucide-react';

const ITEMS_PER_PAGE = 5;

export const HistoryView = ({ logs }: { logs: any[] }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [historyPage, setHistoryPage] = useState(1);

    // [Safety Fix] 確保 logs 是一個陣列，防止 undefined 導致崩潰
    const safeLogs = Array.isArray(logs) ? logs : [];

    const filteredLogs = safeLogs.filter(log => {
        if (!log) return false;
        // [Safety Fix] 確保 note 和 date 存在
        const note = log.note || '';
        const date = log.date || '';
        const searchContent = (note + date).toLowerCase();
        return searchContent.includes(searchTerm.toLowerCase());
    });

    // 排序
    filteredLogs.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    
    const totalPages = Math.ceil(filteredLogs.length / ITEMS_PER_PAGE);
    const startIndex = (historyPage - 1) * ITEMS_PER_PAGE;
    const currentLogs = filteredLogs.slice(startIndex, startIndex + ITEMS_PER_PAGE);

    return (
        <div className="h-full flex flex-col pb-20">
            <div className="flex justify-between items-center mb-6 px-2">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <ListIcon className="text-indigo-400" /> Neural History
                </h2>
                <div className="relative">
                    <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4"/>
                    <input type="text" placeholder="Filter logs..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-9 pr-4 py-2 bg-slate-800 rounded-full text-xs text-white border border-slate-700 focus:border-indigo-500 outline-none w-32 focus:w-48 transition-all"/>
                </div>
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-4 px-2 custom-scrollbar">
                {currentLogs.map((log, i) => {
                    // [Safety Fix] 取值前先給預設值
                    const mood = log.metrics?.mood ?? 5;
                    const focus = log.metrics?.focus ?? 5;
                    const energy = log.metrics?.energy ?? 5;
                    const deepWork = log.metrics?.deepWork ?? 0;
                    const tags = log.graphSeeds?.tags || [];

                    return (
                        <div key={log.date + i} className="bg-[#1e293b] p-5 rounded-2xl border border-slate-700 hover:border-indigo-500/50 transition-colors group relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-bl-full -mr-10 -mt-10 group-hover:bg-indigo-500/10 transition-colors"></div>
                            
                            <div className="flex justify-between items-start mb-3 relative z-10">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400 font-bold text-xs shadow-inner">
                                        <div className="text-center leading-none">
                                            <span className="block text-[10px] uppercase text-slate-500">{new Date(log.date).toLocaleString('en-US', { month: 'short' })}</span>
                                            <span className="text-lg text-white">{new Date(log.date).getDate()}</span>
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-slate-500 font-mono mb-0.5">{new Date(log.date).getFullYear()}</div>
                                        <div className="flex gap-1 flex-wrap">
                                            {/* [Safety Fix] 確保 tags 是陣列 */}
                                            {Array.isArray(tags) && tags.map((tag: string) => (
                                                <span key={tag} className="text-[10px] px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded-full border border-indigo-500/20">#{tag}</span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex gap-1">
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded border flex items-center gap-1 ${mood >= 7 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-slate-700 border-slate-600 text-slate-400'}`}>
                                        <Activity size={10}/> {mood}
                                    </span>
                                </div>
                            </div>
                            
                            <p className="text-sm text-slate-300 leading-relaxed mb-4 relative z-10 line-clamp-3">
                                {log.note || "No content"}
                            </p>
                            
                            <div className="flex justify-between items-center pt-3 border-t border-slate-700/50 relative z-10">
                                <div className="flex gap-3 text-xs text-slate-500">
                                    <span className="flex items-center gap-1"><Zap size={12}/> {energy}</span>
                                    <span className="flex items-center gap-1"><TrendingUp size={12}/> {focus}</span>
                                    <span className="flex items-center gap-1"><Clock size={12}/> {deepWork}h</span>
                                </div>
                                {/* 未來可加入點擊展開詳情 */}
                                <button className="p-1.5 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"><ArrowRight size={14}/></button>
                            </div>
                        </div>
                    );
                })}
                
                {currentLogs.length === 0 && <div className="text-center py-10 text-slate-500 text-sm">No logs found matching &quot;{searchTerm}&quot;</div>}
            </div>
            
            {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-4">
                    {Array.from({ length: totalPages }).map((_, i) => (
                        <button key={i} onClick={() => setHistoryPage(i + 1)} className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${historyPage === i + 1 ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>{i + 1}</button>
                    ))}
                </div>
            )}
        </div>
    );
};