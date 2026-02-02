This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.


prisma/schema.prisma
、、、
generator client {
  provider = "prisma-client-js"
  binaryTargets = ["native", "debian-openssl-1.1.x", "debian-openssl-3.0.x"]
}

datasource db {
  provider  = "postgresql"
  url       = env("POSTGRES_PRISMA_URL")
  directUrl = env("POSTGRES_URL_NON_POOLING")
}

model LogEntry {
  id        String   @id @default(cuid())
  date      DateTime @unique
  content   String
  mood      Int?
  focus     Int?
  energy    Int?
  graphSeeds Json?
  habits    Json?
  isAi      Boolean  @default(false)
  aiModel   String?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  tasks     Task[]
}

model Task {
  id          String    @id @default(cuid())
  title       String
  status      String    @default("PENDING")
  isUrgent    Boolean   @default(false)
  dueDate     DateTime?
  context     String?
  projectId   String?
  project     Project?  @relation(fields: [projectId], references: [id])
  logEntryId  String?
  logEntry    LogEntry? @relation(fields: [logEntryId], references: [id])
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt
}

model Project {
  id          String   @id @default(cuid())
  name        String   @unique
  description String?
  status      String   @default("ACTIVE")
  tasks       Task[]
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

model MonthlyReview {
  id        String   @id @default(cuid())
  month     String   @unique
  content   String
  strategy  Json?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
、、、
lib/ai/core.ts
、、、
// 檔案位置: lib/ai/core.ts
import { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal } from 'lucide-react';

// [核心設定]
export const DEFAULT_HABITS = [
    { id: 'reading', label: '閱讀 Input', icon: 'BookOpen', active: true },
    { id: 'native_coding', label: 'Native Logic', icon: 'Terminal', active: true },
    { id: 'creation', label: '創作 Output', icon: 'Zap', active: true },
    { id: 'exercise', label: '運動 Health', icon: 'Activity', active: true },
    { id: 'meditation', label: '反思 Meta', icon: 'Brain', active: true }
];

export const NEON_PALETTE = {
    EMERALD: '#10b981', ROSE: '#f43f5e', BLUE: '#3b82f6', 
    INDIGO: '#6366f1', SLATE: '#475569', AMBER: '#f59e0b', PINK: '#ec4899'
};

export const CoreEngine = {
    getIconComponent: (iconName: string) => {
        const map: any = { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal };
        return map[iconName] || Star; 
    },
    
    // [Fix] 增強洞察提取邏輯，優先抓取 Drift Point
    extractInsight: (content: string) => {
        if (!content) return { type: 'empty', text: '無文字紀錄', label: 'Empty' };
        
        // 1. 優先偵測 Drift Point (偏移)
        const driftMatch = content.match(/(?:Drift Point|Drift|偏移點)[:：]\s*(.+)/i);
        if (driftMatch && driftMatch[1]) {
            return { type: 'drift', text: driftMatch[1].trim(), label: '⚠️ Drift' };
        }

        // 2. 偵測 Action Check 警告
        if (content.includes('Action Check: ⚠️')) {
            return { type: 'warning', text: 'Action Check Failed', label: '⚠️ Warning' };
        }

        // 3. 抓取 Summary
        const summaryMatch = content.match(/(?:Day Summary|Summary|航行記錄)[:：]\s*(.+)/i);
        if (summaryMatch && summaryMatch[1]) {
            return { type: 'summary', text: summaryMatch[1].trim(), label: '📝 Summary' };
        }

        // 4. 預設：抓取第一行有效內容
        const lines = content.split('\n');
        const preview = lines.find(l => l.length > 5 && !l.startsWith('#') && !l.startsWith('>')) || '無詳細內容';
        return { type: 'general', text: preview.slice(0, 60), label: '📄 Log' };
    },

    parseGraphSeeds: (note: string, graphContent = '') => {
        if (!note) return { tags: [], links: [] };
        const combined = note + ' ' + graphContent;
        const tags = (combined.match(/#([\w\u4e00-\u9fa5]+)/g) || []).map(t => t.slice(1));
        const links = (combined.match(/\[\[(\d{4}-\d{2}-\d{2})\]\]/g) || []).map(l => l.slice(2, -2));
        return { tags: [...new Set(tags)], links: [...new Set(links)] };
    }
};
、、、

app/api/ingest/route.ts
、、、
import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { AGENTIC_INGEST_SYSTEM_PROMPT } from "@/lib/ai/prompts"; //
import { NextResponse } from "next/server";

// 確保使用穩定的模型名稱
const MODEL_NAME = "gemini-3-flash-preview"; 

export async function POST(req: Request) {
  try {
    // 1. [檢查點] 確認環境變數是否存在
    if (!process.env.GEMINI_API_KEY) {
      console.error("❌ Critical: GEMINI_API_KEY is missing in environment variables.");
      return NextResponse.json({ success: false, error: "Server Config Error: Missing API Key" }, { status: 500 });
    }

    const { text, date } = await req.json();
    console.log(`🚀 [Ingest] Processing for ${date} with model ${MODEL_NAME}`);

    // 2. 初始化 AI
    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ 
      model: MODEL_NAME, 
      generationConfig: { responseMimeType: "application/json" } 
    });

    const userPrompt = `CURRENT DATE: ${date}\nINPUT RAW DATA:\n${text}`;

    // 3. [檢查點] 呼叫 AI (並捕捉特定錯誤)
    console.log("🤖 [Ingest] Calling Gemini API...");
    let result;
    try {
        result = await model.generateContent({
          contents: [{ role: "user", parts: [{ text: AGENTIC_INGEST_SYSTEM_PROMPT + "\n\n" + userPrompt }] }]
        });
    } catch (aiError: any) {
        console.error("❌ [Ingest] Gemini API Call Failed:", aiError);
        return NextResponse.json({ success: false, error: `AI Connection Error: ${aiError.message}` }, { status: 502 });
    }
    
    const responseText = result.response.text();
    console.log("✅ [Ingest] AI Response received.");

    // 4. [檢查點] 解析 JSON
    let data: any;
    try {
        data = JSON.parse(responseText);
    } catch (parseError) {
        console.error("❌ [Ingest] JSON Parse Failed. Raw text:", responseText);
        // 如果解析失敗，回傳原始文字讓你知道發生什麼事
        return NextResponse.json({ success: false, error: "AI returned invalid JSON", raw: responseText }, { status: 500 });
    }

    // 5. 製作簽名檔
    // 注意：這裡移除了 PROMPT_VERSION 的引用，因為你的 imports 可能沒包含它
    const aiSignature = `\n\n> 🤖 **AI Insight** | Model: ${MODEL_NAME}`;
    const finalContent = data.markdown_body + aiSignature;

    // 6. 資料庫寫入
    console.log("💾 [Ingest] Writing to Database...");
    await prisma.$transaction(async (tx) => {
      const existingLog = await tx.logEntry.findUnique({ where: { date: new Date(data.meta.date) } });

      let log;
      if (existingLog) {
        log = await tx.logEntry.update({
          where: { date: new Date(data.meta.date) },
          data: {
            content: existingLog.content + "\n\n---\n\n" + finalContent,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy,
            // [New] 寫入模型資訊 (Schema 需支援這些欄位，若無請先移除這兩行)
            // aiModel: MODEL_NAME, 
            // isAi: true
          }
        });
      } else {
        log = await tx.logEntry.create({
          data: {
            date: new Date(data.meta.date),
            content: finalContent,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy,
            // [New] 寫入模型資訊
            // aiModel: MODEL_NAME,
            // isAi: true,
            habits: data.habits || undefined
          }
        });
      }

      // 任務寫入
      if (data.tasks?.length) {
        for (const t of data.tasks) {
          const projectName = t.project_tag || "Inbox";
          const proj = await tx.project.upsert({ where: { name: projectName }, update: {}, create: { name: projectName } });
          await tx.task.create({
            data: {
              title: t.title,
              context: t.context,
              dueDate: t.due_date ? new Date(t.due_date) : null,
              isUrgent: t.category === "urgent",
              projectId: proj.id,
              logEntryId: log.id,
              status: "PENDING"
            }
          });
        }
      }
    });

    console.log("✨ [Ingest] Success!");
    return NextResponse.json({ success: true, model: MODEL_NAME, data });

  } catch (error: any) {
    console.error("🔥 [Ingest] Unhandled Error:", error);
    // 回傳具體錯誤訊息給前端
    return NextResponse.json({ success: false, error: error.message || "Internal Server Error" }, { status: 500 });
  }

}
、、、

app/page.tsx
、、、
'use client';

import React, { useState, useEffect } from 'react';
import { 
    Menu, X, PenTool, Layers, List as ListIcon, Activity, 
    Settings, LayoutTemplate
} from 'lucide-react';
import { CaptureView } from '@/components/CaptureView';
import { GraphView } from '@/components/GraphView';
import { HistoryView } from '@/components/HistoryView';
import { SettingsView } from '@/components/SettingsView';
import { Dashboard } from '@/components/Dashboard';
import { ProjectBoard } from '@/components/ProjectBoard';

// --- MOCK DATA ---
const MOCK_LOGS = [
  { date: '2024-01-30', note: 'Deep work on LifeOS UI #coding', metrics: { mood: 7, focus: 9 }, graphSeeds: { tags: ['coding'], links: [] }, habits: {} },
];

export default function Home() {
  const [logs, setLogs] = useState<any[]>(MOCK_LOGS);
  const [activeTab, setActiveTab] = useState<'capture' | 'graph' | 'list' | 'settings' | 'dashboard' | 'project'>('capture');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  // [Fix] 防止 Hydration Error (水合錯誤)
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
      setIsMounted(true); // 標記元件已掛載
      const saved = localStorage.getItem('life_os_logs_v8_0');
      if (saved) try { setLogs(JSON.parse(saved)); } catch(e) { console.error(e); }
  }, []);

  useEffect(() => {
      if (logs !== MOCK_LOGS) localStorage.setItem('life_os_logs_v8_0', JSON.stringify(logs));
  }, [logs]);

  const handleSaveLog = (newLog: any) => {
      setLogs(prev => [newLog, ...prev]);
      setActiveTab('graph');
  };

  const handleImportLogs = (importedLogs: any[]) => {
      setLogs(prev => [...prev, ...importedLogs]);
  };

  // [Fix] 如果還沒掛載，只回傳一個空殼，避免 Server/Client 不一致
  if (!isMounted) {
      return <div className="h-screen bg-[#f8fafc]"></div>; 
  }

  const bgClass = activeTab === 'graph' ? 'bg-[#0f172a] text-slate-200' : 'bg-[#f8fafc] text-slate-800';

  const menuItems = [
      { id: 'capture', label: '日誌輸入', icon: PenTool },
      { id: 'graph', label: '神經網絡', icon: Layers },
      { id: 'dashboard', label: 'CCA 戰略', icon: Activity },
      { id: 'project', label: '專案戰情', icon: LayoutTemplate },
      { id: 'list', label: '歷史足跡', icon: ListIcon },
      { id: 'settings', label: '系統設定', icon: Settings },
  ];

  return (
    <div className={`max-w-md mx-auto h-screen flex flex-col font-sans relative shadow-2xl overflow-hidden transition-colors duration-500 ${bgClass}`}>
        
        {/* Header */}
        <header className={`px-6 py-4 z-50 flex justify-between items-center border-b sticky top-0 backdrop-blur-sm ${activeTab === 'graph' ? 'border-slate-800 bg-[#0f172a]/90' : 'border-slate-200 bg-white/80'}`}>
            <h1 className={`text-lg font-black tracking-tight ${activeTab === 'graph' ? 'text-white' : 'text-slate-800'}`}>
                LifeOS <span className="text-indigo-500 text-xs align-top px-1">v2.1</span>
            </h1>
            
            <button onClick={() => setIsMenuOpen(!isMenuOpen)} className={`p-2 rounded-full transition-all ${activeTab === 'graph' ? 'hover:bg-slate-800 text-white' : 'hover:bg-slate-100 text-slate-600'}`}>
                {isMenuOpen ? <X size={20}/> : <Menu size={20}/>}
            </button>
        </header>

        {/* Dropdown Menu */}
        {isMenuOpen && (
            <div className="absolute top-16 right-4 z-[100] w-48 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 animate-scale-in origin-top-right">
                {menuItems.map((item) => (
                    <button 
                        key={item.id}
                        onClick={() => { setActiveTab(item.id as any); setIsMenuOpen(false); }}
                        className={`w-full text-left px-4 py-3 flex items-center gap-3 text-sm font-bold transition-colors ${activeTab === item.id ? 'text-indigo-600 bg-indigo-50' : 'text-slate-600 hover:bg-slate-50'}`}
                    >
                        <item.icon size={16} />
                        {item.label}
                    </button>
                ))}
            </div>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-0 relative z-10 custom-scrollbar">
            {activeTab === 'capture' && <CaptureView onSave={handleSaveLog} />}
            {activeTab === 'graph' && <GraphView logs={logs} />}
            {activeTab === 'dashboard' && <Dashboard />}
            {activeTab === 'project' && <ProjectBoard logs={logs} />} 
            {activeTab === 'list' && <HistoryView logs={logs} />}
            {activeTab === 'settings' && <SettingsView logs={logs} onImport={handleImportLogs} />}
        </main>
    </div>
  );
}
、、、

components
、、、
CaptureView.tsx
ContextModal.tsx
Dashboard.tsx
GraphView.tsx
HistoryView.tsx
NeuralGraph.tsx
ProjectBoard.tsx
SettingsView.tsx
、、、

components/CaptureView.tsx
、、、
'use client';

import React, { useState, useEffect } from 'react';
import { PenTool, Cpu, Activity, Terminal, CheckCircle, AlertTriangle } from 'lucide-react';
import { CoreEngine, DEFAULT_HABITS } from '@/lib/ai/core';

export const CaptureView = ({ onSave }: { onSave: (log: any) => void }) => {
    const [entry, setEntry] = useState<any>({ 
        date: '', note: '', mood: 5, focus: 5, energy: 5, deepWork: 0, habits: {} 
    });
    const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
    const [aiThinkingLogs, setAiThinkingLogs] = useState<string[]>([]);
    const [detectedTasks, setDetectedTasks] = useState<string[]>([]);

    useEffect(() => {
        setEntry((prev: any) => ({ ...prev, date: new Date().toISOString().split('T')[0] }));
    }, []);

    // [Fix] 這是真正的 AI 呼叫邏輯，不再是 setTimeout 模擬
    const handleAIParse = async () => {
        if (!entry.note) return alert("❌ 請輸入內容");
        
        setIsAiAnalyzing(true);
        setAiThinkingLogs(["連線神經網絡...", "正在讀取脈絡..."]);
        
        try {
            const response = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: entry.note, 
                    date: entry.date 
                })
            });

            // [Fix] 檢查是否為 JSON 格式
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                // 如果回傳的是 HTML (通常是錯誤頁面)，讀取文字並拋出錯誤
                const text = await response.text();
                console.error("Server Error (HTML):", text); // 在 Console 顯示 HTML 內容以便除錯
                throw new Error("伺服器發生內部錯誤 (500)，請檢查 Terminal 的報錯訊息。");
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || "API 回應錯誤");
            }

            // ... (成功處理邏輯保持不變)
            setAiThinkingLogs(prev => [...prev, "✅ 分析完成", `Model: ${result.model || 'Gemini'}`]);
            
            const aiData = result.data || {};
            const metrics = aiData.meta?.metrics || {};

            setEntry((prev: any) => ({
                ...prev,
                note: result.data.markdown_body,
                mood: metrics.mood ?? prev.mood,
                focus: metrics.focus ?? prev.focus,
                energy: metrics.energy ?? prev.energy,
            }));

            if (aiData.tasks && Array.isArray(aiData.tasks)) {
                setDetectedTasks(aiData.tasks.map((t: any) => t.title));
                setAiThinkingLogs(prev => [...prev, `⚡ 提取了 ${aiData.tasks.length} 個行動`]);
            }

        } catch (e: any) {
            console.error("AI Error:", e);
            setAiThinkingLogs(prev => [...prev, `❌ 錯誤: ${e.message}`]);
            alert(`連線失敗: ${e.message}`);
        } finally {
            setIsAiAnalyzing(false);
        }
    };

    const handleSave = () => {
        const seeds = CoreEngine ? CoreEngine.parseGraphSeeds(entry.note) : { tags: [], links: [] };
        onSave({ ...entry, graphSeeds: seeds });
        // 重置
        setEntry({ date: new Date().toISOString().split('T')[0], note: '', mood: 5, focus: 5, energy: 5, deepWork: 0, habits: {} });
        setDetectedTasks([]);
        setAiThinkingLogs([]);
    };

    return (
        <div className="h-full overflow-y-auto pb-32 px-4 pt-6 custom-scrollbar">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                   <PenTool className="text-indigo-500" /> Capture Flow
                </h2>
                <p className="text-slate-400 text-xs mt-1">紀錄當下，讓 AI 幫你整理結構</p>
            </div>
            
            {/* AI Terminal */}
            {(isAiAnalyzing || aiThinkingLogs.length > 0) && (
                <div className="mb-6 bg-slate-900 rounded-2xl p-4 shadow-xl border border-slate-800">
                    <div className="flex items-center gap-2 mb-2 border-b border-slate-800 pb-2">
                        <Terminal size={14} className="text-emerald-400 animate-pulse"/>
                        <span className="text-xs font-mono text-emerald-400 font-bold">AI_CORE_PROCESSOR</span>
                    </div>
                    <div className="font-mono text-xs space-y-1 h-32 overflow-y-auto custom-scrollbar flex flex-col-reverse">
                        {isAiAnalyzing && <div className="text-emerald-500 animate-pulse">_</div>}
                        {[...aiThinkingLogs].reverse().map((log, i) => (
                            <div key={i} className="text-slate-300"><span className="text-indigo-500 mr-2">➜</span>{log}</div>
                        ))}
                    </div>
                </div>
            )}

            {/* Input Card */}
            <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-200">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Daily Log</span>
                    <input type="date" value={entry.date} onChange={e => setEntry({...entry, date: e.target.value})} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1 text-sm font-mono text-slate-600 outline-none"/>
                </div>
                <textarea 
                    value={entry.note} onChange={e => setEntry({...entry, note: e.target.value})}
                    placeholder="# 輸入想法...\n> Agent 會幫你整理成 Project 與 Life 雙軌"
                    className="w-full h-48 p-4 bg-slate-50 border border-slate-100 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-100 outline-none resize-none leading-relaxed text-slate-700 placeholder:text-slate-400"
                />
                
                {detectedTasks.length > 0 && (
                    <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
                        <div className="text-xs font-bold text-indigo-500 mb-2 flex items-center gap-2"><CheckCircle size={12}/> Extracted Tasks</div>
                        <ul className="space-y-1">
                            {detectedTasks.map((t, i) => <li key={i} className="text-xs text-indigo-700 flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>{t}</li>)}
                        </ul>
                    </div>
                )}

                <div className="flex justify-end gap-2 mt-4">
                    <button onClick={handleAIParse} disabled={isAiAnalyzing} className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 transition-colors flex items-center gap-2">
                        <Cpu className={`w-3 h-3 ${isAiAnalyzing ? 'animate-pulse' : ''}`}/> AI Agent
                    </button>
                    <button onClick={handleSave} className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200 flex items-center gap-2">
                        <Activity className="w-3 h-3"/> Save
                    </button>
                </div>
            </div>
            
            {/* Habits Grid */}
            <div className="grid grid-cols-2 gap-3 mt-4">
                {DEFAULT_HABITS.map(habit => {
                    const isActive = entry.habits?.[habit.id] || false;
                    const Icon = CoreEngine ? CoreEngine.getIconComponent(habit.icon) : Activity;
                    return (
                        <button key={habit.id} onClick={() => setEntry({ ...entry, habits: { ...entry.habits, [habit.id]: !isActive } })}
                            className={`p-4 rounded-2xl border transition-all flex items-center justify-between shadow-sm ${isActive ? 'bg-slate-800 border-slate-800 text-white' : 'bg-white border-slate-100 text-slate-500 hover:bg-slate-50'}`}>
                            <span className="text-xs font-bold">{habit.label}</span>
                            <Icon className={`w-5 h-5 ${isActive ? 'opacity-100' : 'opacity-20'}`} />
                        </button>
                    );
                })}
            </div>

            {/* Sliders */}
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-5 mt-4">
                {['mood', 'focus', 'energy'].map(k => (
                    <div key={k} className="flex items-center gap-4">
                        <label className="w-16 text-xs font-bold text-slate-400 uppercase">{k}</label>
                        <input type="range" min="0" max="10" value={entry[k]} onChange={e => setEntry({...entry, [k]: parseInt(e.target.value)})} className="flex-1 h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-500"/>
                        <span className="w-6 text-right text-sm font-bold text-indigo-600">{entry[k]}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
、、、

// 檔案位置: components/GraphView.tsx
、、、
'use client';

import React, { useState } from 'react';
import { Activity } from 'lucide-react';
import { NeuralGraph } from '@/components/NeuralGraph';
import { ContextModal } from '@/components/ContextModal'; // [New]

export const GraphView = ({ logs }: { logs: any[] }) => {
    const [contextNode, setContextNode] = useState(null);

    return (
        <div className="h-full flex flex-col">
            <ContextModal mainNode={contextNode} logs={logs} onClose={() => setContextNode(null)} />
            
            <div className="flex-1 relative overflow-hidden rounded-2xl border border-slate-800 bg-[#0b1120]">
               <NeuralGraph logs={logs} onNodeClick={setContextNode} />
            </div>
            <div className="p-4 text-center text-slate-500 text-xs">
               <Activity className="w-3 h-3 inline mr-1"/> 
               目前共有 {logs.length} 個節點正在運作
            </div>
        </div>
    );
};
、、、

// 檔案位置: components/NeuralGraph.tsx
、、、
'use client';

import React, { useEffect, useRef, memo, useState } from 'react';
import * as d3 from 'd3';
import { Activity, Layers, LayoutGrid } from 'lucide-react';
import { NEON_PALETTE, CoreEngine } from '@/lib/ai/core';

interface LogNode extends d3.SimulationNodeDatum {
  id: string;
  val: number;
  label: string;
  color: string;
  group?: string;
  raw?: any;
  isSignal?: boolean;
  x?: number;
  y?: number;
}

interface LogLink extends d3.SimulationLinkDatum<LogNode> {
  type: string;
  tag?: string;
}

// [Fix 1] 命名元件函式，而不是使用匿名函式
const NeuralGraphComponent = ({ logs, onNodeClick }: { logs: any[], onNodeClick: (n:any)=>void }) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [mode, setMode] = useState('gravity');
    const [stats, setStats] = useState({ nodes: 0, links: 0 });
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

    useEffect(() => {
        if (!containerRef.current) return;
        const resizeObserver = new ResizeObserver((entries) => {
            if (!entries || entries.length === 0) return;
            const { width, height } = entries[0].contentRect;
            if (width > 0 && height > 0) {
                setDimensions({ width, height });
            }
        });
        resizeObserver.observe(containerRef.current);
        return () => resizeObserver.disconnect();
    }, []);

    useEffect(() => {
        if (!logs || logs.length === 0 || !svgRef.current || dimensions.width === 0) return;
        
        // [Fix 2] 捕捉目前的 ref 值，確保 cleanup 時能正確存取
        const currentSvgRef = svgRef.current;
        const { width, height } = dimensions;
        let simulation: d3.Simulation<LogNode, LogLink> | null = null;

        try {
            const nodesMap = new Map<string, LogNode>();
            const links: LogLink[] = [];

            logs.forEach(log => {
                const id = log.date;
                const noteContent = typeof log.note === 'string' ? log.note : '';
                const graphContent = log.graphSeeds?.content || '';
                const seeds = CoreEngine ? CoreEngine.parseGraphSeeds(noteContent, graphContent) : { tags: [], links: [] };
                
                if (!nodesMap.has(id)) {
                    const mood = Number(log.metrics?.mood || 5);
                    const focus = Number(log.metrics?.focus || 5);
                    let color = NEON_PALETTE.INDIGO;
                    
                    if (log.isSignal) color = NEON_PALETTE.BLUE;
                    else if (mood > 7) color = NEON_PALETTE.EMERALD;
                    else if (mood < 4) color = NEON_PALETTE.ROSE;

                    nodesMap.set(id, { 
                        id, 
                        val: 10 + (focus * 1.5),
                        label: id.slice(5), 
                        color, 
                        raw: log,
                        x: width / 2 + (Math.random() - 0.5) * 50,
                        y: height / 2 + (Math.random() - 0.5) * 50
                    });
                }
                
                seeds.tags.forEach((tag: string) => {
                    if(!nodesMap.has(tag)) {
                        nodesMap.set(tag, { 
                            id: tag, 
                            val: 8, 
                            label: tag, 
                            color: NEON_PALETTE.PINK, 
                            group: 'tag',
                            x: width / 2,
                            y: height / 2
                        });
                    }
                    links.push({ source: id, target: tag, type: 'tag' });
                });

                seeds.links.forEach((target: string) => {
                      if (!nodesMap.has(target)) {
                          nodesMap.set(target, {
                              id: target,
                              val: 5,
                              label: target,
                              color: NEON_PALETTE.SLATE,
                              group: 'stub',
                              x: width / 2,
                              y: height / 2
                          });
                      }
                      links.push({ source: id, target: target, type: 'manual' });
                });
            });

            const nodes = Array.from(nodesMap.values());
            setStats(prev => (prev.nodes === nodes.length ? prev : { nodes: nodes.length, links: links.length }));

            const svg = d3.select(currentSvgRef);
            svg.selectAll("*").remove();

            const g = svg.append("g");
            
            simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id((d:any) => d.id).distance(60))
                .force("charge", d3.forceManyBody().strength(mode === 'cluster' ? -50 : -120))
                .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))
                .force("collide", d3.forceCollide().radius((d:any) => d.val + 4).iterations(2));

            const link = g.append("g")
                .selectAll("line")
                .data(links)
                .join("line")
                .attr("stroke", "#6366f1")
                .attr("stroke-opacity", 0.2)
                .attr("stroke-width", (d:any) => d.type === 'manual' ? 1.5 : 1)
                .attr("stroke-dasharray", (d:any) => d.type === 'tag' ? "3,3" : "");

            // SVG Defs (Glow Filter)
            const defs = svg.append("defs");
            const filter = defs.append("filter").attr("id", "glow");
            filter.append("feGaussianBlur").attr("stdDeviation", "2.5").attr("result", "coloredBlur");
            const feMerge = filter.append("feMerge");
            feMerge.append("feMergeNode").attr("in", "coloredBlur");
            feMerge.append("feMergeNode").attr("in", "SourceGraphic");

            const node = g.append("g")
                .selectAll("g")
                .data(nodes)
                .join("g")
                .call(d3.drag<any, any>()
                    .on("start", (e, d) => { if (!e.active) simulation?.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
                    .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
                    .on("end", (e, d) => { if (!e.active) simulation?.alphaTarget(0); d.fx = null; d.fy = null; })
                )
                .on("click", (e, d) => { 
                    e.stopPropagation(); 
                    onNodeClick(d.raw || { id: d.id, label: d.label, group: d.group }); 
                });

            node.append("circle")
                .attr("r", (d:any) => d.val)
                .attr("fill", (d:any) => d.color)
                .attr("stroke", "#1e293b")
                .attr("stroke-width", 2)
                .style("filter", "url(#glow)")
                .style("cursor", "pointer");

            node.append("text")
                .text((d:any) => d.label)
                .attr("text-anchor", "middle")
                .attr("dy", (d:any) => d.val + 12)
                .attr("fill", "#94a3b8")
                .attr("font-size", "10px")
                .style("pointer-events", "none")
                .style("user-select", "none");

            simulation.on("tick", () => {
                link
                    .attr("x1", (d:any) => d.source.x)
                    .attr("y1", (d:any) => d.source.y)
                    .attr("x2", (d:any) => d.target.x)
                    .attr("y2", (d:any) => d.target.y);
                node
                    .attr("transform", (d:any) => `translate(${d.x},${d.y})`);
            });

            const zoom = d3.zoom().scaleExtent([0.1, 5]).on("zoom", (e) => {
                g.attr("transform", e.transform);
            });
            svg.call(zoom as any);

        } catch (error) {
            console.error("D3 Graph Error:", error);
        }

        return () => {
            if (simulation) simulation.stop();
            // 使用變數中的 ref 進行 cleanup
            if (currentSvgRef) {
                d3.select(currentSvgRef).on(".zoom", null);
                currentSvgRef.innerHTML = "";
            }
        };

    // [Fix 3] 加入 onNodeClick 到依賴陣列
    }, [logs, mode, dimensions, onNodeClick]);

    return (
        <div ref={containerRef} className="w-full h-[500px] bg-[#0b1120] rounded-3xl overflow-hidden relative border border-slate-800 shadow-2xl">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-2 pointer-events-none">
                <div className="bg-slate-900/80 px-3 py-1 rounded-full text-xs text-emerald-400 font-mono flex items-center gap-2 border border-emerald-500/30 backdrop-blur">
                    <Activity size={12}/> Neon D3 Engine: ACTIVE
                </div>
                <div className="text-[10px] text-slate-500 font-mono ml-2">
                    Nodes: {stats.nodes} | Links: {stats.links}
                </div>
            </div>
            
            <div className="absolute top-4 right-4 z-20 flex gap-2">
                <button onClick={() => setMode('gravity')} className={`p-2 rounded-lg border transition-all ${mode==='gravity'?'bg-indigo-600 border-indigo-400 text-white':'bg-slate-800 border-slate-700 text-slate-400'}`}><Layers size={16}/></button>
                <button onClick={() => setMode('cluster')} className={`p-2 rounded-lg border transition-all ${mode==='cluster'?'bg-indigo-600 border-indigo-400 text-white':'bg-slate-800 border-slate-700 text-slate-400'}`}><LayoutGrid size={16}/></button>
            </div>

            <svg ref={svgRef} className="w-full h-full cursor-move block"></svg>
        </div>
    );
};

// [Fix 4] 設定 Display Name 並 Memo 化
export const NeuralGraph = memo(NeuralGraphComponent);
NeuralGraph.displayName = 'NeuralGraph';
、、、
components/ContextModal.tsx
、、、
// 檔案位置: components/ContextModal.tsx
'use client';
import React from 'react';
import { Network, X, Link as LinkIcon, Calendar, Hash } from 'lucide-react';

export const ContextModal = ({ mainNode, logs, onClose }: { mainNode: any, logs: any[], onClose: () => void }) => {
    if (!mainNode) return null;

    // [Fix] 增強關聯邏輯：大小寫不敏感，並支援 Graph Link
    const relatedLogs = logs.map(log => {
        const note = (log.note || '').toLowerCase();
        const nodeId = (mainNode.id || '').toLowerCase();
        let reason = null;

        // 1. Tag 匹配
        if (mainNode.group === 'tag' && (note.includes(`#${nodeId}`) || (log.graphSeeds?.tags || []).some((t:string) => t.toLowerCase() === nodeId))) {
            reason = { type: 'tag', label: `#${mainNode.label}` };
        } 
        // 2. 日期匹配
        else if (mainNode.group === 'date' && log.date === mainNode.id) {
            reason = { type: 'date', label: 'Same Day' };
        } 
        // 3. 直接連結 (Link)
        else if (log.graphSeeds?.links?.includes(mainNode.id)) {
            reason = { type: 'link', label: 'Linked' };
        }

        return reason ? { ...log, matchReason: reason } : null;
    }).filter(Boolean);

    return (
        <div className="fixed inset-0 z-[150] flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-sm animate-fade-in" onClick={onClose}>
            <div className="w-full max-w-lg max-h-[85vh] bg-white rounded-3xl shadow-2xl flex flex-col border border-slate-200" onClick={e => e.stopPropagation()}>
                
                {/* Header */}
                <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-3xl">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-100 rounded-full text-indigo-600"><Network size={20}/></div>
                        <div>
                            <h3 className="font-bold text-xl text-slate-800">{mainNode.label}</h3>
                            <span className="text-xs text-slate-400 uppercase font-mono">Cluster ({relatedLogs.length})</span>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors"><X size={20}/></button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-5 space-y-3 custom-scrollbar">
                    {relatedLogs.length > 0 ? (
                        relatedLogs.map((log: any, i) => (
                            <div key={i} className="bg-white p-4 rounded-xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all group">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-xs font-mono text-slate-400 bg-slate-50 px-2 py-1 rounded">{log.date}</span>
                                    
                                    <span className={`text-[10px] px-2 py-1 rounded-full flex items-center gap-1 font-bold ${
                                        log.matchReason.type === 'tag' ? 'bg-pink-100 text-pink-600' :
                                        log.matchReason.type === 'date' ? 'bg-indigo-100 text-indigo-600' :
                                        'bg-blue-100 text-blue-600'
                                    }`}>
                                        {log.matchReason.type === 'tag' && <Hash size={10}/>}
                                        {log.matchReason.type === 'date' && <Calendar size={10}/>}
                                        {log.matchReason.type === 'link' && <LinkIcon size={10}/>}
                                        {log.matchReason.label}
                                    </span>
                                </div>
                                <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed">{log.note || log.content}</p>
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-10 text-slate-400 italic">
                            此節點 ({mainNode.label}) 暫無關聯日記。
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// 檔案位置: components/SettingsView.tsx
'use client';
import React, { useState } from 'react'; // [Add] useState
import { Download, Upload, Database, Terminal, Copy } from 'lucide-react'; // [Add] Terminal, Copy
// [Add] 引入 Prompt 內容 (需確保 lib/ai/prompts.ts 有正確 export 這些字串)
import { DAILY_INGEST_PROMPT, MONTHLY_REVIEW_PROMPT } from '@/lib/ai/prompts';

export const SettingsView = ({ logs, onImport }: { logs: any[], onImport: (data: any)=>void }) => {
    // [New] Prompt State
    const [prompts, setPrompts] = useState({
        daily: DAILY_INGEST_PROMPT,
        monthly: MONTHLY_REVIEW_PROMPT
    });
    
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
            {/* [New Section] System Prompts */}
            <div className="bg-[#1e293b] p-6 rounded-3xl shadow-lg border border-slate-700">
                 <h3 className="text-base font-bold text-slate-300 mb-4 flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-emerald-500"/> System Prompts
                 </h3>
                 <div className="space-y-4">
                    {[ {l:'Daily Ingest', k:'daily'}, {l:'Monthly Review', k:'monthly'} ].map(p => (
                        <div key={p.k}>
                            <div className="flex justify-between items-center mb-1">
                                <label className="text-xs font-bold text-slate-500 uppercase">{p.l}</label>
                                <button onClick={() => navigator.clipboard.writeText((prompts as any)[p.k])} className="text-[10px] bg-slate-800 px-2 py-1 rounded flex gap-1 text-slate-400 hover:text-white"><Copy size={12}/> Copy</button>
                            </div>
                            <textarea 
                                value={(prompts as any)[p.k]} 
                                readOnly // 暫時設為唯讀，因為實際修改需由後端代碼控制
                                className="w-full h-24 bg-slate-900 border border-slate-800 rounded-xl p-3 text-[10px] font-mono resize-none outline-none text-slate-400" 
                            />
                        </div>
                    ))}
                 </div>
            </div>

            {/* Data Management (原有的部分) */}
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
、、、

app/core/config_manager.py
import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.system import SystemConfig
import time

class ConfigManager:
    _instance = None
    _cache = {}
    _cache_ttl = 300  # 5分鐘快取

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def get_value(self, key: str, default: str) -> str:
        current_time = time.time()
        
        # 1. 檢查快取
        if key in self._cache:
            val, timestamp = self._cache[key]
            if current_time - timestamp < self._cache_ttl:
                return val

        # 2. 讀取資料庫
        db: Session = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                self._cache[key] = (config.value, current_time)
                return config.value
        except Exception as e:
            print(f"Config DB Read Error: {e}")
        finally:
            db.close()

        # 3. 回退至環境變數或預設值
        return os.getenv(key, default)

    def set_value(self, key: str, value: str):
        db: Session = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not config:
                config = SystemConfig(key=key, value=value)
                db.add(config)
            else:
                config.value = value
            
            db.commit()
            # 更新快取
            self._cache[key] = (value, time.time())
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

config_manager = ConfigManager()

backend-cortex/app/api/v1/ingest.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.sorter import SorterAgent

router = APIRouter()
agent = SorterAgent()

class IngestRequest(BaseModel):
    content: str
    source: str = "web"

@router.post("/ingest")
async def ingest_log(request: IngestRequest):
    try:
        # 1. AI 思考與結構化
        structured_log = agent.process(request.content)
        
        # 2. (TODO) 這裡未來會呼叫 Supabase 寫入 DB
        # database.save(structured_log)
        
        return {
            "status": "success", 
            "data": structured_log.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

  backend-cortex/app/agents/sorter.py
  import os
from google import genai
from dotenv import load_dotenv
from app.models.gemini import LogEntry

load_dotenv()

class SorterAgent:
    def __init__(self):
        # 使用 Flash 模型進行快速分類
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = "gemini-2.0-flash" 

    def process(self, user_input: str) -> LogEntry:
        prompt = f"""
        你是一個極速分類器 (The Sorter)。
        請分析以下使用者輸入，並將其結構化。
        
        使用者輸入: {user_input}
        """
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": LogEntry, # 關鍵：強制結構化輸出
            },
        )
        
        # 自動轉為 Pydantic Object，無需再做 JSON.parse
        return response.parsed

  backend-cortex/app/models/gemini.py
  from pydantic import BaseModel, Field
from typing import List, Optional

class LogEntry(BaseModel):
    """將使用者的輸入轉化為結構化日誌"""
    category: str = Field(..., description="分類標籤 (e.g., Work, Life, Idea)")
    tags: List[str] = Field(..., description="相關標籤")
    summary: str = Field(..., description="一句話總結")
    mood_score: int = Field(..., description="情緒分數 1-10", ge=1, le=10)
    action_items: List[str] = Field(default=[], description="需要執行的下一步行動")

backend-cortex/requirements.txt
fastapi
uvicorn
google-genai
pydantic
python-dotenv
