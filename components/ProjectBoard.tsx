// 檔案位置: components/ProjectBoard.tsx
'use client';
import React from 'react';
import { LayoutTemplate, ChevronRight, Hash } from 'lucide-react';

export const ProjectBoard = ({ logs }: { logs: any[] }) => {
    // [Fix] 安全聚合邏輯
    const projectMap = new Map();
    
    (logs || []).forEach(log => {
        // 安全存取 tags，若 undefined 則用空陣列
        const tags = log.graphSeeds?.tags || [];
        tags.forEach((tag: string) => {
            if (!projectMap.has(tag)) {
                projectMap.set(tag, { name: tag, count: 0, lastUpdate: log.date });
            }
            const p = projectMap.get(tag);
            p.count++;
            if (new Date(log.date) > new Date(p.lastUpdate)) p.lastUpdate = log.date;
        });
    });
    
    const projects = Array.from(projectMap.values()).sort((a,b) => b.count - a.count);

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 custom-scrollbar">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                   <LayoutTemplate className="text-indigo-500" /> Projects
                </h2>
                <p className="text-slate-400 text-xs mt-1">從日誌標籤自動聚合的專案狀態</p>
            </div>

            <div className="grid grid-cols-1 gap-3">
                {projects.map((proj) => (
                    <div key={proj.name} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex justify-between items-center group cursor-pointer hover:border-indigo-300 transition-all">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-500 transition-colors">
                                <Hash size={18}/>
                            </div>
                            <div>
                                <h3 className="font-bold text-slate-700">{proj.name}</h3>
                                <span className="text-xs text-slate-400">Last Active: {proj.lastUpdate}</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="text-xs font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded-full">{proj.count} logs</span>
                            <ChevronRight size={16} className="text-slate-300"/>
                        </div>
                    </div>
                ))}
                {projects.length === 0 && <div className="text-center py-10 text-slate-400">尚無專案標籤 (#Tag)，請在日記中使用 #專案名</div>}
            </div>
        </div>
    );
};