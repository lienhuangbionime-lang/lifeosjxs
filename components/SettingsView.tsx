// 檔案位置: components/SettingsView.tsx
'use client';
import React from 'react';
import { Download, Upload, Database } from 'lucide-react';

export const SettingsView = ({ logs, onImport }: { logs: any[], onImport: (data: any)=>void }) => {
    
    const handleExport = () => {
        const bundle = { 
            version: "v2.0 (Cloud)", 
            logs: logs, 
            timestamp: new Date().toISOString() 
        };
        const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a'); 
        link.href = url; 
        link.download = `life_os_backup_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link); link.click(); document.body.removeChild(link);
    };

    const handleFileImport = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]; if (!file) return;
        const reader = new FileReader();
        reader.onload = async (ev) => {
            try {
                const json = JSON.parse(ev.target?.result as string);
                const logsToImport = Array.isArray(json) ? json : (json.logs || []);
                
                if (confirm(`準備匯入 ${logsToImport.length} 筆資料到雲端資料庫，這可能需要一點時間。確定嗎？`)) {
                    // 目前僅更新前端狀態，未來可接批次寫入 API
                    onImport(logsToImport); 
                    alert("✅ 匯入成功 (暫存於本地)");
                }
            } catch (err) { alert("❌ 格式錯誤"); }
        };
        reader.readAsText(file);
    };

    return (
        <div className="space-y-6 pb-24 animate-fade-in">
            <div className="bg-[#1e293b] p-6 rounded-3xl shadow-lg border border-slate-700 space-y-4">
                <h3 className="text-base font-bold text-slate-300 flex items-center gap-2"><Database className="w-4 h-4 text-indigo-500"/> Data Management</h3>
                
                <div className="flex gap-2">
                    <button onClick={handleExport} className="flex-1 py-3 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-xl text-xs font-bold flex justify-center items-center gap-2 hover:bg-indigo-500/20 transition-all">
                        <Download className="w-4 h-4"/> Backup JSON
                    </button>
                    <label className="flex-1 py-3 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-xl text-xs font-bold flex justify-center items-center gap-2 cursor-pointer hover:bg-emerald-500/20 transition-all">
                        <Upload className="w-4 h-4"/> Restore JSON
                        <input type="file" className="hidden" onChange={handleFileImport} accept=".json"/>
                    </label>
                </div>

                <div className="p-3 bg-slate-800 rounded-xl text-xs text-slate-500 leading-relaxed">
                    ℹ️ <b>v2.0 架構說明：</b><br/>
                    目前匯入功能僅更新前端顯示。完整的「雲端遷移」功能將在後續實作。
                </div>
            </div>
        </div>
    );
};