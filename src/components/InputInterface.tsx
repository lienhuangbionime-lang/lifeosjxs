"use client";
import React, { useState } from 'react';
import { Edit3, Cpu, Save, Copy, ExternalLink, ListTodo } from 'lucide-react';

export const InputInterface = ({ onSaveEntry }: { onSaveEntry: (data: any) => void }) => {
    const [note, setNote] = useState("");
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [aiTasks, setAiTasks] = useState<string[]>([]);

    const handleAIAgent = async () => {
        setIsProcessing(true);
        try {
            const res = await fetch('/api/ingest', {
                method: 'POST',
                body: JSON.stringify({ text: note, date })
            });
            const result = await res.json();
            
            if (result.success) {
                // 更新 UI
                const tasks = result.data.tasks?.map((t: any) => t.title) || [];
                setAiTasks(tasks);
                onSaveEntry(result.data); // 通知父元件更新
                setNote(result.data.markdown_body); // 回填整理好的 Markdown
            }
        } catch (e) {
            console.error(e);
            alert("Agent Error");
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="space-y-6 pb-24 animate-fade-in">
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-bold text-slate-600 flex items-center gap-2"><Edit3 className="w-4 h-4"/> DAILY LOG</span>
                    <input type="date" value={date} onChange={e => setDate(e.target.value)} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1 text-sm font-mono outline-none"/>
                </div>
                <textarea 
                    value={note} onChange={e => setNote(e.target.value)}
                    placeholder="輸入原始想法..."
                    className="w-full h-40 p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-100 outline-none resize-none leading-relaxed"
                />
                
                {/* Task Bridge UI */}
                {aiTasks.length > 0 && (
                    <div className="mt-4 bg-blue-50 border border-blue-100 rounded-xl p-3 animate-fade-in">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-xs font-bold text-blue-600 flex items-center gap-1"><ListTodo size={12}/> Agent Tasks</span>
                        </div>
                        <ul className="space-y-1">
                            {aiTasks.map((t, i) => <li key={i} className="text-xs text-blue-800 flex items-start gap-2">• {t}</li>)}
                        </ul>
                    </div>
                )}

                <div className="flex justify-end gap-2 mt-4">
                    <button onClick={handleAIAgent} disabled={isProcessing} className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 transition-colors flex items-center gap-2">
                        {isProcessing ? <Cpu className="w-3 h-3 animate-pulse"/> : <Cpu className="w-3 h-3"/>} 
                        {isProcessing ? "Thinking..." : "AI Agent"}
                    </button>
                </div>
            </div>
        </div>
    );
};
