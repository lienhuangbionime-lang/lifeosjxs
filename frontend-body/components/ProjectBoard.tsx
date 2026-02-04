'use client';
import React from 'react';
import { LayoutTemplate, ChevronRight, Hash, FolderKanban } from 'lucide-react';

export const ProjectBoard = ({ logs }: { logs: any[] }) => {
    // [Fix] 安全聚合邏輯: 從 #Tags 自動產生專案
    const projectMap = new Map();
    
    (logs || []).forEach(log => {
        // 安全存取 tags，若 undefined 則用空陣列
        // 優先讀取 graphSeeds.tags，兼容 V2 的 tags 欄位
        const tags = log.graphSeeds?.tags || log.tags || [];
        
        tags.forEach((tag: string) => {
            if (!projectMap.has(tag)) {
                projectMap.set(tag, { name: tag, count: 0, lastUpdate: log.date });
            }
            const p = projectMap.get(tag);
            p.count++;
            // 找出最近更新日期
            if (new Date(log.date) > new Date(p.lastUpdate)) p.lastUpdate = log.date;
        });
    });
    
    // 排序：按活躍度 (日誌數量) 降序排列
    const projects = Array.from(projectMap.values()).sort((a,b) => b.count - a.count);

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 custom-scrollbar">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                   <LayoutTemplate className="text-indigo-400" /> Projects
                </h2>
                <p className="text-slate-400 text-xs mt-1">從日誌標籤自動聚合的專案狀態</p>
            </div>

            <div className="grid grid-cols-1 gap-3">
                {projects.map((proj) => (
                    <div key={proj.name} className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-2xl border border-slate-700 shadow-lg flex justify-between items-center group cursor-pointer hover:border-indigo-500/50 hover:bg-slate-800 transition-all">
                        <div className="flex items-center gap-4">
                            {/* Icon Container */}
                            <div className="w-12 h-12 rounded-xl bg-slate-900 flex items-center justify-center text-slate-500 group-hover:bg-indigo-900/30 group-hover:text-indigo-400 transition-colors border border-slate-800 group-hover:border-indigo-500/30">
                                <Hash size={20}/>
                            </div>
                            
                            {/* Text Info */}
                            <div>
                                <h3 className="font-bold text-slate-200 text-lg tracking-tight group-hover:text-white transition-colors">{proj.name}</h3>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                    <span className="text-xs font-mono text-slate-500">Last Active: {proj.lastUpdate}</span>
                                </div>
                            </div>
                        </div>
                        
                        {/* Stats & Arrow */}
                        <div className="flex items-center gap-3">
                            <span className="text-xs font-bold bg-slate-900 border border-slate-700 text-slate-400 px-3 py-1 rounded-full group-hover:text-indigo-300 group-hover:border-indigo-500/30 transition-all">
                                {proj.count} logs
                            </span>
                            <ChevronRight size={18} className="text-slate-600 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all"/>
                        </div>
                    </div>
                ))}
                
                {/* Empty State */}
                {projects.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-slate-500 border-2 border-dashed border-slate-800 rounded-3xl bg-slate-900/20">
                        <FolderKanban size={48} className="mb-4 opacity-20"/>
                        <p className="text-sm">尚無專案標籤</p>
                        <p className="text-xs mt-2 opacity-50">請在 Capture 輸入日誌時使用 #Tag</p>
                    </div>
                )}
            </div>
        </div>
    );
};
