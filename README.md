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


LifeOS v3 系統架構地圖
📋 請複製以下內容到新的 NotebookLM：
# Project Context: LifeOS v3.1 "Autopoiesis"
## 1. 專案願景
我們正在開發 LifeOS v3.1，這是一個「生物化」的個人作業系統。
核心概念是 **Autopoiesis (自生系統)**，系統具備感知、記憶、執行與自我進化的能力。
## 2. 系統架構 (The Anatomy)
採用 **Monorepo** 結構，分為四個視窗 (Windows)：
* **Window 1: The Body (Frontend)**
* **路徑**: `frontend-body/`
* **技術**: Next.js 15, Tailwind CSS (Dark Mode), Lucide Icons.
* **狀態**: 已完成 UI 修復 (Hydration, CSS)、圖譜引擎 (D3 Dynamic Import) 與專案板 (Tag Aggregation)。已植入 `SystemStatus` 元件。
* **部署**: Vercel (已連線 Railway).
* **Window 2 & 3: The Cortex (Backend)**
* **路徑**: `backend-cortex/`
* **技術**: FastAPI, Python 3.11+, Google Gemini SDK (Pro/Flash), APScheduler.
* **核心功能**:
* **Sorter Agent**: 負責快速分類輸入。
* **Architect Agent**: 負責深度思考與對話 (需符合 Pydantic 結構化輸出)。
* **Evolution Agent**: 負責掃描 Google Model Garden 並自動修改 `.env` 升級模型。
* **部署**: Railway (Docker).
* **Window 4: The Hippocampus (Database)**
* **技術**: Supabase (PostgreSQL + pgvector).
* **資料**: 存放 Logs (日誌), Tasks (任務), Thoughts (思考軌跡).
## 3. 目前進度 (Current Status)
1. **前端 (Body)**: 已完成重構。`page.tsx` 已整合 Capture, Graph, Project, SystemStatus。解決了 Hydration 與 TypeScript 錯誤。
2. **後端 (Brain)**: 定義了 `backend-cortex` 目錄結構。
3. **進化協議 (Evolution)**:
* 後端 `api/v1/system.py` 已實作 `POST /upgrade` (修改 .env)。
* 前端 `SystemStatus.tsx` 已實作 UI 與 API 串接。
## 4. 關鍵準則 (Guidelines)
1. **Gemini API 分層**: 使用 Flash 模型處理感知，Pro 模型處理思考。
2. **結構化輸出**: 所有 Agent 必須透過 Pydantic 定義 `response_schema`。
3. **思考簽名**: AI 回應必須包含 `thought_signature` (觀察、情緒、記憶連結)。
## 5. 下一步任務 (Next Steps)
我們需要開始實作 `backend-cortex` 的核心 Agent 邏輯：
1. 完善 `app/core/gemini.py` (Client 封裝)。
2. 實作 `Architect Agent` 的 Prompt 與邏輯。
3. 讓前端的 `CaptureView` 真正打通到 FastAPI 的 `ingest` 端點。

Life-os-v3/
├── README.md                # 📜 [系統宣言] Evolution Protocol 說明
│
├── 📂 frontend-body/        # 🟦 Window 1: The Body (Next.js 15)
│   ├── next.config.js       # ⚙️ 前端運行配置
│   ├── tailwind.config.ts   # 🎨 樣式配置
│   ├── package.json         # 📦 前端依賴管理
│   ├── 📂 app/              # 🚀 [路由中樞]
│   │   ├── globals.css      # 🎨 全域樣式
│   │   ├── layout.tsx       # 🏗️ UI 佈局骨架
│   │   └── page.tsx         # 🏠 系統首頁入口
│   ├── 📂 components/       # 🎨 [視覺模組] 系統交互器官
│   │   ├── CaptureView.tsx  # 📝 AI Terminal (快取輸入)
│   │   ├── ContextModal.tsx # 🗔 上下文彈窗
│   │   ├── Dashboard.tsx    # 📊 主控面板
│   │   ├── GraphView.tsx    # 🕸️ 圖譜視圖
│   │   ├── HistoryView.tsx  # 📜 歷史回溯 (接軌 Memories API)
│   │   ├── NeuralGraph.tsx  # 🧠 神經關聯圖
│   │   ├── ProjectBoard.tsx # 🏗️ 專案管理面板
│   │   ├── SettingsView.tsx # ⚙️ 系統調節
│   │   └── SystemStatus.tsx # 🧬 系統進化 (接軌 System API)
│   └── 📂 lib/              # 🔌 [神經傳導]
│       ├── 📂 ai/           # 🧠 前端 AI 核心函數 (core.ts)
│       └── 📂 api/          # 🌐 API Client (client.ts)
│
├── 📂 backend-cortex/       # 🟧 & 🟪 Window 2 & 3: The Cortex (FastAPI)
│   ├── main.py              # 🚪 應用程式入口 (掛載 Routers & Scheduler)
│   ├── requirements.txt     # 📦 Python 核心依賴 (fastapi, uvicorn, supabase, google-genai)
│   ├── .env                 # 🔑 [私鑰] GEMINI_API_KEY, SUPABASE_URL/KEY
│   └── 📂 app/              # 🧠 [大腦邏輯層]
│       ├── 📂 core/         # ⚙️ [核心基礎設施]
│       │   ├── config.py    # 🔧 環境變數管理
│       │   ├── database.py  # 💾 Database Client (supabase-py 單例)
│       │   └── gemini.py    # 🤖 Model Factory (Client 初始化 & get_model)
│       ├── 📂 models/       # 📐 [資料結構]
│       │   └── schemas.py   # 📝 Pydantic Models (LogEntry, API Response)
│       ├── 📂 api/          # 🌐 [皮質接口] (Routers)
│       │   └── 📂 v1/
│       │       ├── ingest.py    # 📥 感知輸入 (處理 CaptureView)
│       │       ├── memories.py  # 💾 記憶檢索 (處理 HistoryView)
│       │       └── system.py    # 🧬 系統狀態 (處理 SystemStatus)
│       └── 📂 subconscious/ # 🌑 [潛意識循環]
│           └── scheduler.py # ⏰ 生物時鐘 (APScheduler 心跳與排程)
│
└── 📂 database-hippocampus/ # 🟩 Window 4: The Hippocampus
    └── 📂 prisma/           # 📐 [核心記憶模板]
        └── schema.prisma    # 📝 唯一記憶真理來源 (Schema Definition Only)

        
 本地版本
 import React, { useState, useEffect, useMemo, useCallback, memo, useRef } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, ComposedChart
} from 'recharts';
import * as d3 from 'd3';
import { 
  Save, Download, Upload, Trash2, Activity, BookOpen, Brain, Zap, 
  Wand2, Footprints, Settings, 
  AlertCircle, Network, 
  AlertTriangle, Target, Rocket, PlusCircle,
  Terminal, Copy, Check, X, Clipboard, Link as LinkIcon, Hash,
  Edit3, Sliders, PlayCircle, StopCircle, Star,
  TrendingUp, Heart, Clock, ArrowRight,
  Filter, Quote, FileText, MapPin, GitMerge,
  Cpu, Eye, ListTodo, ExternalLink
} from 'lucide-react';

// ============================================================================
// 1. 全域設定與常數 (Global Configuration)
// ============================================================================

const VERSION = "10.3 (Task Bridge & Stability)"; 

// [Data Resilience] Legacy Keys retained for stability
const STORAGE_KEY_LOGS = 'life_os_logs_v8_0'; 
const STORAGE_KEY_CONFIG = 'life_os_config_v8_0'; 
const STORAGE_KEY_CCA = 'life_os_cca_v6_5';   
const STORAGE_KEY_SETTINGS = 'life_os_settings_v6_0';
const STORAGE_KEY_PROMPTS = 'life_os_prompts_v7_2';

// [Neon Engine] Visual DNA - Cyberpunk Aesthetic
const NEON_PALETTE = {
    EMERALD: '#10b981', // High Mood / Flow
    ROSE: '#f43f5e',    // Low Mood / Warning
    BLUE: '#3b82f6',    // Deep Work / Signal (Zapier Task)
    INDIGO: '#6366f1',  // Neutral
    SLATE: '#475569',   // Noise / Background
    AMBER: '#f59e0b',   // Project / Drift
    PINK: '#ec4899',    // Tags
    GLOW_COLOR: '#ffffff'
};

const DEFAULT_METRICS = { mood: 5, focus: 5, energy: 5, deepWork: 0 };
const DEFAULT_HABITS = [
    { id: 'reading', label: '閱讀 Input', icon: 'BookOpen', active: true },
    { id: 'native_coding', label: 'Native Logic', icon: 'Terminal', active: true },
    { id: 'creation', label: '創作 Output', icon: 'Zap', active: true },
    { id: 'exercise', label: '運動 Health', icon: 'Activity', active: true },
    { id: 'meditation', label: '反思 Meta', icon: 'Brain', active: true }
];

const DEFAULT_CONFIG = {
    habits: DEFAULT_HABITS,
    targetFocus: 7.0,
    username: "User"
};

const DEFAULT_ENTRY = {
  mood: 5, 
  focus: 5, 
  energy: 5, 
  readingTime: 0,
  habits: {}, 
  note: '',
  graphSeeds: { tags: '', links: '', content: '' } 
};

const DEFAULT_SETTINGS = {
  avatar: "https://api.dicebear.com/7.x/notionists/svg?seed=Felix",
  username: "MY"
};

const DEFAULT_PROMPTS = { monthly: "", daily: "" };

const BIAS_KEYWORDS = ['確認偏誤', '沉沒成本', '過擬合', '爆倉', '手癢', 'App 替代陪伴', 'Core Weakness', '逃避'];

// ============================================================================
// 2. 核心引擎 (Core Engine - OO Optimization)
// ============================================================================

const CoreEngine = {
    // [White Screen Fix] Factory for virtual nodes to prevent crashes
    generateStubLog: (id, group) => {
        return {
            date: id,
            isStub: true, 
            metrics: { mood: 5, focus: 5, energy: 5, deepWork: 0 },
            habits: {},
            note: `## Virtual Node: ${id}\n> Type: ${group || 'Connector'}\n\nThis node exists in the graph but has no log entry yet.`,
            sections: { 
                summary: `🔗 Graph Node: ${id}`, 
                drift: '', 
                blindSpot: '' 
            },
            graphSeeds: { tags: [], links: [], content: '' }
        };
    },

    sanitizeLogEntry: (entry, index) => {
        const safeDate = entry.date || `1970-01-01_${index}`;
        
        let summary = entry.sections?.summary || '';
        if (typeof entry.note === 'string') {
            let match = entry.note.match(/(?:Day Summary|Summary|航行記錄|本日摘要|Highlights)\s*[:：]\s*([^\r\n]+)/i);
            if (!match) {
                match = entry.note.match(/(?:Day Summary|Summary|航行記錄|本日摘要|Highlights)\s*[:：]?\s*[\r\n]+\s*([^\r\n]+)/i);
            }
            if (match && match[1]) {
                const candidate = match[1].trim();
                if (candidate.length > 0 && !candidate.startsWith('#') && !candidate.startsWith('>')) {
                    summary = candidate;
                }
            }
        }

        const noteText = (typeof entry.note === 'string') ? entry.note : '';
        const isHighFocus = (Number(entry.metrics?.focus ?? entry.focus ?? 5) >= 8);
        const hasActionKeywords = /TODO|URGENT|待辦|緊急/i.test(noteText);
        const isSignal = isHighFocus || hasActionKeywords;

        return {
            date: safeDate,
            timestamp: entry.timestamp || Date.now(),
            metrics: { 
                mood: Number(entry.metrics?.mood ?? entry.mood ?? 5), 
                focus: Number(entry.metrics?.focus ?? entry.focus ?? 5), 
                energy: Number(entry.metrics?.energy ?? entry.energy ?? 5), 
                deepWork: Number(entry.metrics?.deepWork ?? entry.readingTime ?? 0)
            },
            habits: entry.habits || {},
            note: noteText,
            graphSeeds: {
                tags: entry.graphSeeds?.tags || '',
                links: entry.graphSeeds?.links || '',
                content: entry.graphSeeds?.content || ''
            },
            isSignal: isSignal,
            sections: {
                summary: summary,
                path: entry.sections?.path || '',
                drift: entry.sections?.drift || '',
                blindSpot: entry.sections?.blindSpot || ''
            }
        };
    },

    sanitizeData: (rawData) => {
        if (!Array.isArray(rawData)) return [];
        return rawData
            .filter(item => item && typeof item === 'object')
            .map(CoreEngine.sanitizeLogEntry)
            .sort((a, b) => new Date(a.date) - new Date(b.date));
    },

    extractInsight: (content) => {
        if (!content) return { type: 'empty', text: '無文字紀錄' };
        
        const foundBias = BIAS_KEYWORDS.find(k => content.includes(k));
        if (foundBias) {
            const sentences = content.split(/[。\n]/);
            const targetSentence = sentences.find(s => s.includes(foundBias)) || foundBias;
            return { type: 'bias', text: targetSentence.trim().slice(0, 60), label: 'Bias' };
        }
        
        const driftMatch = content.match(/(?:Drift Point|偏移點|Drift)[^:\n]*[:：]?\s*(.*)/i);
        if (driftMatch && driftMatch[1] && driftMatch[1].trim() !== 'None') {
            return { type: 'drift', text: driftMatch[1].replace(/\*\*/g, '').trim(), label: 'Drift' };
        }

        const lines = content.split('\n');
        let previewText = '';
        
        for (let line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith('#') || trimmed.includes('Daily Metrics') || trimmed.includes('Mood:') || trimmed.includes('Day Summary')) {
                continue;
            }
            const cleanLine = trimmed.replace(/[>*\-]/g, '').trim();
            if (cleanLine.length > 5) { 
                previewText = cleanLine;
                break; 
            }
        }
        
        const finalText = previewText || '無詳細內容';
        return { type: 'general', text: finalText.slice(0, 80) + (finalText.length > 80 ? '...' : ''), label: 'Log' };
    },

    // [Task Bridge] Extract TODOs
    extractTasks: (content) => {
        if (!content) return [];
        const regex = /(?:- \[ \]|TODO|URGENT|待辦|\[ \])\s*(.*)/gi;
        const tasks = [];
        let match;
        while ((match = regex.exec(content)) !== null) {
            if (match[1] && match[1].trim()) {
                tasks.push(match[1].trim());
            }
        }
        return tasks;
    },

    parseGraphSeeds: (note, graphContent = '') => {
        if (!note || typeof note !== 'string') return { tags: [], links: [] };
        const combinedText = note + ' ' + graphContent;
        const tags = (combinedText.match(/#([\w\u4e00-\u9fa5]+)/g) || []).map(t => t.slice(1)).filter(t => !BIAS_KEYWORDS.includes(t));
        const links = (combinedText.match(/\[\[(\d{4}-\d{2}-\d{2})\]\]/g) || []).map(l => l.slice(2, -2));
        return { tags: [...new Set(tags)], links: [...new Set(links)] };
    },

    getIconComponent: (iconName) => {
        const map = { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal };
        return map[iconName] || Star; 
    }
};

// ============================================================================
// 3. 輔助函數 (Helpers)
// ============================================================================

const safeLoad = (key, fallback) => {
    try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
        console.error(`Storage Load Error: ${key}`, e);
        return fallback;
    }
};

const copyToClipboard = async (text) => {
  if (!text) return false;
  try { await navigator.clipboard.writeText(text); return true; } catch (err) { return false; }
};

// ============================================================================
// 4. 元件 (Components)
// ============================================================================

// [GRAPH v10.2.2] HIGH DENSITY NEON ENGINE - VISUAL STABILITY FIX
const NeuralGraph = memo(({ logs, onNodeClick }) => {
    const svgRef = useRef(null);
    const containerRef = useRef(null);
    const [stats, setStats] = useState({ nodes: 0, links: 0 });

    const graphData = useMemo(() => {
        if (!logs || logs.length === 0) return { nodes: [], links: [] };

        const nodesMap = new Map();
        const links = [];

        logs.forEach(log => {
            const id = log.date;
            const seeds = CoreEngine.parseGraphSeeds(log.note, log.graphSeeds?.content);
            const tags = seeds.tags;
            const explicitLinks = seeds.links;
            
            if (!nodesMap.has(id)) {
                const mood = log.metrics?.mood || 5;
                const isSignal = log.isSignal;
                let color = NEON_PALETTE.INDIGO;
                if (isSignal) color = NEON_PALETTE.BLUE;
                else if (mood > 7) color = NEON_PALETTE.EMERALD;
                else if (mood < 4) color = NEON_PALETTE.ROSE;

                nodesMap.set(id, { 
                    id, 
                    group: 'date', 
                    val: isSignal ? 16 : (8 + (log.metrics.focus * 0.5)),
                    label: id.slice(5),
                    color: color,
                    raw: log,
                    isSignal: isSignal
                });
            }

            tags.forEach(tag => {
                if (!nodesMap.has(tag)) {
                    nodesMap.set(tag, { 
                        id: tag, 
                        group: 'tag', 
                        val: 10, 
                        label: tag,
                        color: NEON_PALETTE.PINK
                    });
                }
                links.push({ source: id, target: tag, type: 'tag' });
            });

            explicitLinks.forEach(targetDate => {
                 if (!nodesMap.has(targetDate)) {
                     nodesMap.set(targetDate, {
                         id: targetDate,
                         group: 'stub',
                         val: 5,
                         label: targetDate.slice(5),
                         color: NEON_PALETTE.SLATE
                     });
                 }
                 links.push({ source: id, target: targetDate, type: 'manual' });
            });
        });

        return { nodes: Array.from(nodesMap.values()), links };
    }, [logs]); 

    useEffect(() => {
        if (!graphData.nodes.length || !svgRef.current || !containerRef.current) return;

        const { clientWidth: width, clientHeight: height } = containerRef.current;
        if (width === 0 || height === 0) return;

        setStats({ nodes: graphData.nodes.length, links: graphData.links.length });

        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove(); 

        const g = svg.append("g"); 
        const linkLayer = g.append("g").attr("class", "links");
        const nodeLayer = g.append("g").attr("class", "nodes");
        const textLayer = g.append("g").attr("class", "labels");

        const zoom = d3.zoom()
            .scaleExtent([0.1, 5])
            .on("zoom", (e) => g.attr("transform", e.transform));
        svg.call(zoom);

        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(60))
            .force("charge", d3.forceManyBody().strength(-120))
            .force("center", d3.forceCenter(width / 2, height / 2).strength(0.08))
            .force("collide", d3.forceCollide().radius(d => d.val + 2).iterations(3));

        const defs = svg.append("defs");
        const filter = defs.append("filter").attr("id", "glow");
        filter.append("feGaussianBlur").attr("stdDeviation", "2.5").attr("result", "coloredBlur");
        const feMerge = filter.append("feMerge");
        feMerge.append("feMergeNode").attr("in", "coloredBlur");
        feMerge.append("feMergeNode").attr("in", "SourceGraphic");

        const link = linkLayer
            .selectAll("line")
            .data(graphData.links)
            .join("line")
            .attr("stroke", "#cbd5e1")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", d => d.type === 'manual' ? 1.5 : 0.8)
            .attr("stroke-dasharray", d => d.type === 'tag' ? "2,2" : "0");

        const node = nodeLayer
            .selectAll("g")
            .data(graphData.nodes)
            .join("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .filter(d => d.isSignal)
            .attr("r", d => d.val + 6)
            .attr("fill", d => d.color)
            .attr("opacity", 0.4)
            .style("filter", "url(#glow)");

        node.append("circle")
            .attr("r", d => d.val)
            .attr("fill", d => d.color)
            .attr("stroke", "#0f172a")
            .attr("stroke-width", 2)
            .style("cursor", "pointer")
            .on("click", (e, d) => { 
                e.stopPropagation(); 
                const nodeData = d.raw ? { ...d.raw, group: d.group } : { id: d.id, label: d.label, group: d.group, tags: [], data: { note: "Stub Node" } };
                onNodeClick(nodeData); 
            })
            .on("mouseover", function() { d3.select(this).transition().duration(200).attr("stroke", "#fff").attr("stroke-width", 3); })
            .on("mouseout", function() { d3.select(this).transition().duration(200).attr("stroke", "#0f172a").attr("stroke-width", 2); });

        const label = textLayer
            .selectAll("text")
            .data(graphData.nodes)
            .join("text")
            .attr("dy", d => d.val + 12)
            .attr("text-anchor", "middle")
            .text(d => d.label.length > 8 ? d.label.slice(0,6)+'..' : d.label)
            .attr("fill", "#94a3b8")
            .attr("font-size", "9px")
            .attr("font-family", "monospace")
            .style("pointer-events", "none")
            .style("text-shadow", "0 2px 4px rgba(0,0,0,1)");

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${d.x},${d.y})`);
            label.attr("x", d => d.x).attr("y", d => d.y);
        });

        function dragstarted(e, d) {
            if (!e.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        function dragged(e, d) {
            d.fx = e.x;
            d.fy = e.y;
        }
        function dragended(e, d) {
            if (!e.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return () => simulation.stop();

    }, [graphData]); 

    return (
        <div ref={containerRef} className="w-full h-[500px] bg-slate-900 rounded-3xl overflow-hidden relative border border-slate-800 shadow-2xl">
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-1 pointer-events-none select-none">
                <div className="bg-slate-900/80 px-3 py-1 rounded-full text-xs text-emerald-400 font-mono flex items-center gap-2 border border-emerald-500/30 backdrop-blur">
                    <Activity size={12}/> Neon D3 Engine: STABLE
                </div>
                <div className="text-[10px] text-slate-500 font-mono ml-2">
                    Nodes: {stats.nodes} | Links: {stats.links}
                </div>
            </div>
            <svg ref={svgRef} className="w-full h-full cursor-move"></svg>
        </div>
    );
});

const MarkdownRenderer = memo(({ content }) => {
    if (!content) return <div className="text-slate-300 italic text-sm text-center py-10">尚無內容</div>;
    return (
        <div className="space-y-3 text-slate-700 text-sm font-mono leading-relaxed">
            {content.split('\n').map((line, i) => {
                if (line.startsWith('# ')) return <h3 key={i} className="text-lg font-bold text-indigo-700 mt-4 border-b border-indigo-100 pb-1">{line.replace('# ', '')}</h3>;
                if (line.startsWith('## ')) return <h4 key={i} className="text-base font-bold text-slate-800 mt-3 flex items-center gap-2"><div className="w-1 h-4 bg-indigo-500 rounded-full"/>{line.replace('## ', '')}</h4>;
                if (line.startsWith('> ')) return <div key={i} className="border-l-4 border-indigo-200 pl-3 py-2 my-2 bg-slate-50 text-slate-600 italic rounded-r-lg">{line.replace('> ', '')}</div>;
                return <p key={i} className="min-h-[1em]">{line}</p>;
            })}
        </div>
    );
});

// [White Screen Fix] Context Cluster Modal
const ContextModal = ({ mainNode, logs, onClose, onOpenEntry }) => {
    const connections = useMemo(() => {
        if (!mainNode) return [];
        
        const mainId = mainNode.id;
        // Use CoreEngine to parse seeds
        const mainSeeds = CoreEngine.parseGraphSeeds(mainNode.note, mainNode.graphSeeds?.content);
        const mainTags = mainSeeds.tags.length > 0 ? mainSeeds.tags : (mainNode.group === 'tag' ? [mainId] : []);
        const mainLinks = mainSeeds.links;

        let mainLog = logs.find(l => l.date === mainId);
        
        // [Safety Check] Generate Stub Log if real log doesn't exist to prevent crash
        if (!mainLog) {
            mainLog = CoreEngine.generateStubLog(mainId, mainNode.group);
            mainLog.connectionReason = 'Current Focus';
        } else {
             mainLog.connectionReason = 'Current Focus'; 
        }

        const related = logs.filter(l => {
            if (l.date === mainId) return false;
            const logSeeds = CoreEngine.parseGraphSeeds(l.note, l.graphSeeds?.content);
            const logTags = logSeeds.tags;
            const logLinks = logSeeds.links;
            
            const sharedTags = logTags.filter(t => mainTags.includes(t));
            const isLinked = logLinks.includes(mainId) || mainLinks.includes(l.date);
            const isTaggedWithMain = (mainNode.group === 'tag') && logTags.includes(mainId);

            if (sharedTags.length > 0 || isLinked || isTaggedWithMain) {
                if (isLinked) l.connectionReason = 'Direct Link';
                else if (isTaggedWithMain) l.connectionReason = 'Tagged';
                else l.connectionReason = `#${sharedTags[0]}`;
                return true;
            }
            return false;
        }).slice(0, 10); 
        
        return [mainLog, ...related];
    }, [mainNode, logs]);

    if (!mainNode) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm animate-fade-in" onClick={onClose}>
            <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto custom-scrollbar bg-transparent flex flex-col gap-4 animate-scale-in" onClick={e => e.stopPropagation()}>
                <div className="flex items-center gap-2 text-white/80 pb-2 border-b border-white/10">
                    <Network className="w-5 h-5"/>
                    <span className="font-bold text-lg tracking-tight">Context Cluster: {mainNode.id}</span>
                </div>
                {connections.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {connections.map((conn, idx) => (
                            <div key={conn.date} onClick={() => onOpenEntry(conn)} 
                                className={`rounded-xl p-4 cursor-pointer hover:scale-[1.01] transition-all shadow-lg border-l-4 group relative overflow-hidden ${idx === 0 ? 'bg-indigo-50 border-indigo-500 ring-2 ring-indigo-200' : 'bg-white/95 backdrop-blur hover:bg-white border-slate-300'}`}>
                                <div className="flex justify-between items-center mb-1">
                                    <span className="font-bold text-slate-800 text-sm flex items-center gap-2">{conn.date} {idx === 0 && <MapPin size={12} className="text-indigo-600"/>}</span>
                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${idx === 0 ? 'bg-indigo-100 text-indigo-700 border-indigo-200' : 'bg-slate-100 text-slate-600 border-slate-200'}`}>{conn.connectionReason}</span>
                                </div>
                                <p className="text-xs text-slate-500 line-clamp-2">{CoreEngine.extractInsight(conn.note).text}</p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-white/50 text-center py-10 italic">No direct connections found.</div>
                )}
            </div>
        </div>
    );
};

const ConfirmModal = ({ isOpen, title, message, onConfirm, onCancel }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center p-4 animate-fade-in">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-all" onClick={onCancel} />
      <div className="bg-white/95 w-full max-w-xs rounded-3xl shadow-2xl p-6 relative z-10 animate-scale-in text-center border border-white/20 backdrop-blur-md">
        <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4"><AlertCircle className="w-6 h-6 text-red-500" /></div>
        <h3 className="text-lg font-bold text-slate-800 mb-2">{title}</h3>
        <p className="text-sm text-slate-500 mb-6 leading-relaxed">{message}</p>
        <div className="flex gap-3">
          <button onClick={onCancel} className="flex-1 py-3 bg-slate-100 text-slate-600 rounded-2xl font-bold text-sm hover:bg-slate-200">取消</button>
          <button onClick={onConfirm} className="flex-1 py-3 bg-red-500 text-white rounded-2xl font-bold text-sm hover:bg-red-600 shadow-lg">確定</button>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// 6. 主程式 (Main App)
// ============================================================================

const LifeOS = () => {
    const [activeTab, setActiveTab] = useState('input');
    const [notification, setNotification] = useState(null);
    const [selectedEntry, setSelectedEntry] = useState(null); 
    const [contextNode, setContextNode] = useState(null); 
    const [confirmState, setConfirmState] = useState({ isOpen: false, title: '', message: '', action: null });
    const [detectedTasks, setDetectedTasks] = useState([]); // [Task Bridge] State

    // Data
    const [logs, setLogs] = useState(() => CoreEngine.sanitizeData(safeLoad(STORAGE_KEY_LOGS, [])));
    const [config, setConfig] = useState(() => safeLoad(STORAGE_KEY_CONFIG, DEFAULT_CONFIG));
    const [userSettings, setUserSettings] = useState(() => safeLoad(STORAGE_KEY_SETTINGS, DEFAULT_SETTINGS));
    const [prompts, setPrompts] = useState(() => safeLoad(STORAGE_KEY_PROMPTS, DEFAULT_PROMPTS)); 
    const [ccaData, setCcaData] = useState(() => safeLoad(STORAGE_KEY_CCA, {}));

    // Input State
    const [entry, setEntry] = useState({ date: new Date().toISOString().split('T')[0], ...DEFAULT_ENTRY });
    const [newHabitName, setNewHabitName] = useState(''); 
    const [dashboardMonth, setDashboardMonth] = useState(new Date().toISOString().slice(0, 7));
    const [isEditingReview, setIsEditingReview] = useState(false);

    useEffect(() => {
        if (!entry.date) setEntry(prev => ({ ...prev, date: new Date().toISOString().split('T')[0] }));
    }, []);

    useEffect(() => {
        try { localStorage.setItem(STORAGE_KEY_LOGS, JSON.stringify(logs)); } 
        catch (e) { showToast("❌ 儲存失敗：空間不足", "error"); }
    }, [logs]);

    useEffect(() => { localStorage.setItem(STORAGE_KEY_CONFIG, JSON.stringify(config)); }, [config]);
    useEffect(() => { localStorage.setItem(STORAGE_KEY_PROMPTS, JSON.stringify(prompts)); }, [prompts]);
    useEffect(() => { localStorage.setItem(STORAGE_KEY_CCA, JSON.stringify(ccaData)); }, [ccaData]);

    const showToast = (msg, type='success') => { setNotification({msg, type}); setTimeout(() => setNotification(null), 3000); };

    const handleSaveEntry = () => {
        const finalSeeds = { 
            tags: entry.graphSeeds?.tags || '', 
            links: entry.graphSeeds?.links || '', 
            content: entry.graphSeeds?.content || '' 
        };
        
        let finalNote = entry.note;
        if (!finalNote) {
            finalNote = `# [${entry.date}] Log\n> Mood: ${entry.mood} | Focus: ${entry.focus}\n\n## Summary\n${entry.graphSeeds?.tags ? `Tags: ${entry.graphSeeds.tags}` : ''}`;
        }
        
        if ((entry.habits['creation'] || entry.habits['native_coding']) && entry.readingTime < 15 && !finalNote.includes('Core Weakness')) {
            finalNote += "\n\n⚠️ [Warning: Core Weakness]";
            showToast("⚠️ 偵測到核心能力虛弱", "warning");
        }

        const newEntry = {
            ...entry,
            metrics: { mood: entry.mood, focus: entry.focus, energy: entry.energy, deepWork: entry.readingTime }, 
            graphSeeds: finalSeeds,
            note: finalNote,
            timestamp: Date.now()
        };

        setLogs(prev => {
            const filtered = prev.filter(l => l.date !== newEntry.date);
            return [...filtered, CoreEngine.sanitizeLogEntry(newEntry)].sort((a,b) => new Date(a.date) - new Date(b.date));
        });
        showToast("✅ 紀錄已寫入 (Neural Sync)");
        setEntry(prev => ({ ...DEFAULT_ENTRY, date: prev.date })); 
        setDetectedTasks([]); // Clear tasks after save
    };

    // [AI Agent Fix] Enhanced Regex Logic for Multi-line content & Task Extraction
    const handleAIParse = () => {
        const text = entry.note;
        if (!text) return;
        
        const mood = text.match(/(?:Mood|心情)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const focus = text.match(/(?:Focus|專注)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const energy = text.match(/(?:Energy|能量)[\s\S]*?(\d+(?:\.\d+)?)/i);
        const deep = text.match(/(?:Deep|Reading|深度)[\s\S]*?(\d+(?:\.\d+)?)/i);
        
        const dateMatch = text.match(/(?:Date|日期|^#\s*\[?)?\s*(\d{4}-\d{2}-\d{2})/m);
        const targetDate = dateMatch ? dateMatch[1] : entry.date;

        const graphMatch = text.match(/(?:Graph|Connections|關聯)(?:[\s:：]*)(?:[\r\n]+)([\s\S]*?)(?:$|^#)/mi);
        const graphContent = graphMatch ? graphMatch[1].trim() : '';

        const searchScope = graphContent || text;
        const tags = (searchScope.match(/#([\w\u4e00-\u9fa5]+)/g) || []).join(' ');
        const links = (searchScope.match(/\[\[(.*?)\]\]/g) || []).join(' ');

        let detectedFocus = focus ? parseInt(focus[1]) : entry.focus;
        if (text.includes('URGENT') || text.includes('TODO')) {
            detectedFocus = Math.max(detectedFocus || 5, 8); 
        }

        let detectedHabits = { ...entry.habits };
        config.habits.forEach(h => {
            if (text.toLowerCase().includes(h.id) || text.includes(h.label.split(' ')[0])) {
                detectedHabits[h.id] = true;
            }
        });
        
        // [Task Bridge] Extract tasks
        const tasks = CoreEngine.extractTasks(text);
        setDetectedTasks(tasks);

        setEntry(prev => ({
            ...prev,
            date: targetDate,
            mood: mood ? parseInt(mood[1]) : prev.mood,
            focus: detectedFocus,
            energy: energy ? parseInt(energy[1]) : prev.energy,
            readingTime: deep ? parseInt(deep[1]) : prev.readingTime,
            habits: detectedHabits,
            graphSeeds: { tags: tags, links: links, content: graphContent } 
        }));
        showToast(`🪄 AI 分析完成 (提取 ${tasks.length} 個待辦)`);
    };

    const requestDelete = (date) => setConfirmState({ isOpen: true, title: '刪除紀錄', message: `確定要刪除 ${date} 的紀錄嗎？`, action: () => {
        setLogs(prev => prev.filter(d => d.date !== date));
        setSelectedEntry(null);
        setConfirmState({ isOpen: false });
        showToast("🗑️ 紀錄已刪除");
    }});

    const requestClear = () => setConfirmState({ isOpen: true, title: '清空資料', message: '確定要清空所有資料嗎？', action: () => {
        setLogs([]); localStorage.removeItem(STORAGE_KEY_LOGS);
        setConfirmState({ isOpen: false }); showToast("🧹 已清空");
    }});

    const addNewHabit = () => {
        if (!newHabitName.trim()) return;
        const newHabit = { id: `custom_${Date.now()}`, label: newHabitName, icon: 'Star', active: true };
        setConfig({ ...config, habits: [...config.habits, newHabit] });
        setNewHabitName('');
    };
    const toggleHabit = (id) => {
        const newHabits = config.habits.map(h => h.id === id ? { ...h, active: !h.active } : h);
        setConfig({ ...config, habits: newHabits });
    };

    const handleUpdateCCA = (month, field, value) => {
        setCcaData(prev => ({ ...prev, [month]: { ...prev[month], [field]: value } }));
    };

    const executeSystemUpgrade = (month) => {
        const reviewText = ccaData[month]?.review;
        if (!reviewText) { showToast("❌ 無內容", "error"); return; }
        const regex = /\[ADD\]\s*habit:(.*)/g;
        let match, addedCount = 0;
        const newHabits = [...config.habits];
        while ((match = regex.exec(reviewText)) !== null) {
            const habitName = match[1].trim();
            if (!newHabits.some(h => h.label === habitName) && habitName !== 'NA') {
                newHabits.push({ id: `evo_${Date.now()}_${addedCount}`, label: habitName, icon: 'Rocket', active: true });
                addedCount++;
            }
        }
        if (addedCount > 0) { 
            setConfig({ ...config, habits: newHabits }); 
            showToast(`🚀 系統升級: +${addedCount} 習慣`); 
        } else showToast("⚠️ 無新指令", "warning");
    };

    const handleChartClick = useCallback((data) => {
        if (data && data.activePayload && data.activePayload.length > 0) {
            const payload = data.activePayload[0].payload;
            setSelectedEntry(payload);
        }
    }, []);

    const handleExport = () => {
        const bundle = { 
            version: VERSION, 
            logs: logs, 
            config: config, 
            settings: userSettings, 
            prompts: prompts, 
            cca: ccaData 
        };
        const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a'); 
        link.href = url; 
        link.download = `life_os_backup_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link); link.click(); document.body.removeChild(link);
    };

    const handleImport = (e) => {
        const file = e.target.files[0]; if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            try { 
                const json = JSON.parse(ev.target.result); 
                if(json.logs) setLogs(CoreEngine.sanitizeData(json.logs)); 
                if(json.config) {
                    const existingIds = new Set(config.habits.map(h => h.id));
                    const newHabits = json.config.habits.filter(h => !existingIds.has(h.id));
                    setConfig({ ...json.config, habits: [...config.habits, ...newHabits] });
                }
                if(json.prompts) setPrompts(json.prompts);
                if(json.cca) setCcaData(json.cca);
                showToast("✅ 還原成功：包含 CCA/Prompts/Logs"); 
            } 
            catch(err) { showToast("❌ 格式錯誤", "error"); }
        }; reader.readAsText(file);
    };

    // --- Sub-Views ---

    const renderInputTab = () => (
        <div className="space-y-6 pb-24 animate-fade-in">
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-bold text-slate-600 flex items-center gap-2"><Edit3 className="w-4 h-4"/> DAILY LOG</span>
                    <input type="date" value={entry.date} onChange={e => setEntry({...entry, date: e.target.value})} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1 text-sm font-mono outline-none"/>
                </div>
                <textarea 
                    value={entry.note} onChange={e => setEntry({...entry, note: e.target.value})}
                    placeholder="# [YYYY-MM-DD] Title\n> Mood: 8 | Focus: 7\n[T:30] (S) Task...\n\n## Graph\n#ProjectA [[2024-01-01]]"
                    className="w-full h-40 p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-mono focus:ring-2 focus:ring-indigo-100 outline-none resize-none leading-relaxed"
                />
                
                {/* [Task Bridge] UI Section */}
                {detectedTasks.length > 0 && (
                    <div className="mt-4 bg-blue-50 border border-blue-100 rounded-xl p-3 animate-fade-in">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-xs font-bold text-blue-600 flex items-center gap-1"><ListTodo size={12}/> AI Task Bridge</span>
                            <div className="flex gap-2">
                                <button onClick={() => { copyToClipboard(detectedTasks.join('\n')); showToast("Tasks Copied!"); }} className="text-[10px] bg-white px-2 py-1 rounded border border-blue-200 text-blue-600 hover:bg-blue-100 flex items-center gap-1"><Copy size={10}/> Copy All</button>
                                <a href="https://tasks.google.com/embed/?origin=https://mail.google.com" target="_blank" rel="noopener noreferrer" className="text-[10px] bg-blue-600 px-2 py-1 rounded text-white hover:bg-blue-700 flex items-center gap-1"><ExternalLink size={10}/> Open GTasks</a>
                            </div>
                        </div>
                        <ul className="space-y-1">
                            {detectedTasks.map((t, i) => (
                                <li key={i} className="text-xs text-blue-800 flex items-start gap-2">
                                    <span className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0"></span>
                                    {t}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className="mt-4 pt-4 border-t border-slate-100 flex flex-col gap-3">
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                        <div className="flex items-center gap-2 mb-2 text-slate-400 text-xs font-bold uppercase tracking-wider"><GitMerge size={12}/> Graph Context</div>
                        <textarea 
                            placeholder="Paste your ## Graph section here or let AI parse it..." 
                            value={entry.graphSeeds?.content || ''} 
                            onChange={e => setEntry({...entry, graphSeeds: {...entry.graphSeeds, content: e.target.value}})} 
                            className="bg-transparent w-full text-xs font-mono outline-none text-slate-700 placeholder:text-slate-300 resize-none h-16"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="bg-indigo-50 p-2 rounded-xl flex items-center gap-2 border border-indigo-100">
                            <Hash className="w-4 h-4 text-indigo-400"/>
                            <input placeholder="Tags" value={entry.graphSeeds?.tags || ''} onChange={e => setEntry({...entry, graphSeeds: {...entry.graphSeeds, tags: e.target.value}})} className="bg-transparent w-full text-xs font-mono outline-none text-indigo-800 placeholder:text-indigo-300"/>
                        </div>
                        <div className="bg-indigo-50 p-2 rounded-xl flex items-center gap-2 border border-indigo-100">
                            <LinkIcon className="w-4 h-4 text-indigo-400"/>
                            <input placeholder="Links" value={entry.graphSeeds?.links || ''} onChange={e => setEntry({...entry, graphSeeds: {...entry.graphSeeds, links: e.target.value}})} className="bg-transparent w-full text-xs font-mono outline-none text-indigo-800 placeholder:text-indigo-300"/>
                        </div>
                    </div>
                </div>
                <div className="flex justify-end gap-2 mt-4">
                    <button onClick={handleAIParse} className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 transition-colors flex items-center gap-2"><Cpu className="w-3 h-3"/> AI Agent</button>
                    <button onClick={handleSaveEntry} className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200 flex items-center gap-2"><Save className="w-3 h-3"/> Save</button>
                </div>
            </div>
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-4">
                {[ {k:'mood', c:'indigo', l:'Mood'}, {k:'focus', c:'rose', l:'Focus'}, {k:'energy', c:'amber', l:'Energy'}, {k:'readingTime', c:'blue', l:'Deep Work', m:240, s:10} ].map(m => (
                    <div key={m.k} className="flex items-center gap-4">
                        <label className="w-20 text-xs font-bold text-slate-400 uppercase">{m.l}</label>
                        <input type="range" min="0" max={m.m||10} step={m.s||1} value={entry[m.k]} onChange={e => setEntry({...entry, [m.k]: parseInt(e.target.value)})} className={`flex-1 h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-${m.c}-500`}/>
                        <span className={`w-8 text-right text-sm font-black text-${m.c}-500`}>{entry[m.k]}</span>
                    </div>
                ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
                 {config.habits.filter(h => h.active).map(habit => {
                     const Icon = CoreEngine.getIconComponent(habit.icon); const isActive = entry.habits[habit.id];
                     return (
                       <button key={habit.id} onClick={() => setEntry({...entry, habits: {...entry.habits, [habit.id]: !isActive}})} 
                           className={`p-4 rounded-2xl border transition-all flex items-center justify-between ${isActive ? 'bg-slate-800 border-slate-800 text-white shadow-lg' : 'bg-white border-slate-100 text-slate-400'}`}>
                         <span className="text-xs font-bold">{habit.label}</span><Icon className={`w-5 h-5 ${isActive ? 'opacity-100' : 'opacity-20'}`} />
                       </button>
                     );
                 })}
            </div>
        </div>
    );

    const renderDashboard = () => {
        if (!logs || logs.length === 0) return <div className="text-center py-20 text-slate-400">數據累積中...</div>;
        
        const filteredLogs = logs.filter(l => l.date.startsWith(dashboardMonth));
        const data = filteredLogs.sort((a,b) => new Date(a.date) - new Date(b.date));

        return (
            <div className="space-y-6 pb-24 animate-fade-in">
                <div className="flex justify-between items-center bg-white p-3 rounded-2xl shadow-sm border border-slate-100">
                    <div className="flex items-center gap-2 text-slate-700">
                        <Filter className="w-4 h-4 text-indigo-500" />
                        <span className="text-sm font-bold">Month View</span>
                    </div>
                    <input type="month" value={dashboardMonth} onChange={(e) => setDashboardMonth(e.target.value)} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-sm font-mono outline-none focus:ring-2 focus:ring-indigo-100" />
                </div>

                <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-200 h-64">
                    <h3 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2"><Activity className="w-4 h-4 text-indigo-500"/> 近期趨勢 (Recent Trends)</h3>
                    <div style={{ width: '100%', height: '100%', minHeight: '200px' }}>
                        <ResponsiveContainer>
                            <ComposedChart data={data} onClick={handleChartClick} style={{cursor:'pointer'}}>
                                <defs><linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#6366f1" stopOpacity={0.2}/><stop offset="95%" stopColor="#6366f1" stopOpacity={0}/></linearGradient></defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9"/>
                                <XAxis dataKey="date" tick={{fontSize:10}} tickFormatter={v=>v.slice(8)} axisLine={false} tickLine={false}/>
                                <YAxis yAxisId="left" orientation="left" stroke="#6366f1" hide domain={[0, 10]}/>
                                <YAxis yAxisId="right" orientation="right" stroke="#3b82f6" hide/>
                                <Tooltip contentStyle={{borderRadius:'12px', border:'none'}}/>
                                <Area yAxisId="left" type="monotone" dataKey="metrics.mood" stroke="#6366f1" fill="url(#colorMood)" strokeWidth={3}/>
                                <Line yAxisId="left" type="monotone" dataKey="metrics.focus" stroke="#f43f5e" strokeWidth={2} dot={false}/>
                                <Bar yAxisId="right" dataKey="metrics.deepWork" fill="#93c5fd" opacity={0.3} barSize={20} radius={[4,4,0,0]}/>
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-100">
                     <div className="flex justify-between items-center mb-4">
                         <div className="flex items-center gap-2"><Target className="w-4 h-4 text-emerald-500"/><h3 className="text-sm font-bold text-slate-700">月度復盤 (CCA)</h3></div>
                         <div className="flex gap-2">
                             <button onClick={() => setIsEditingReview(!isEditingReview)} className="p-1.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-500">{isEditingReview ? <Eye className="w-3 h-3"/> : <Edit3 className="w-3 h-3"/>}</button>
                             <button onClick={() => executeSystemUpgrade(dashboardMonth)} className="text-[10px] bg-emerald-50 text-emerald-600 px-3 py-1 rounded-lg hover:bg-emerald-100 font-bold flex items-center gap-1 border border-emerald-200"><Rocket className="w-3 h-3"/> 升級系統</button>
                         </div>
                     </div>
                     {isEditingReview ? (
                        <textarea value={ccaData[dashboardMonth]?.review || ''} onChange={(e) => handleUpdateCCA(dashboardMonth, 'review', e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm resize-none outline-none h-48 font-mono" placeholder="貼上報告..." />
                     ) : (
                        <div className="h-48 overflow-y-auto text-sm text-slate-600 font-mono bg-slate-50 p-3 rounded-xl custom-scrollbar border border-slate-100">
                            {ccaData[dashboardMonth]?.review ? <MarkdownRenderer content={ccaData[dashboardMonth].review} /> : <span className="text-slate-400 italic flex flex-col items-center justify-center h-full gap-2"><FileText className="w-6 h-6 opacity-20"/>請貼上報告...</span>}
                        </div>
                     )}
                </div>
            </div>
        );
    };

    const renderHistoryView = () => {
        const historyLogs = [...logs].reverse();
        const getPreviewText = (text) => {
            if (!text) return '無詳細內容';
            return CoreEngine.extractInsight(text).text;
        };

        return (
            <div className="space-y-4 pb-24 animate-fade-in">
              <div className="flex justify-between items-center mb-4"><h3 className="text-base font-bold text-slate-700 px-1">近期足跡 ({historyLogs.length})</h3></div>
              {historyLogs.map((log) => {
                const insight = CoreEngine.extractInsight(log.note);
                const isDrift = insight.type === 'drift';
                const m = log.metrics?.mood ?? 5; 
                const moodColor = m >= 8 ? 'bg-emerald-400' : m <= 3 ? 'bg-red-400' : 'bg-indigo-400';
                const activeHabits = Object.keys(log.habits).filter(h => log.habits[h]);

                return (
                  <div key={log.date} onClick={() => setSelectedEntry(log)} className={`group p-5 rounded-3xl border relative cursor-pointer hover:shadow-lg transition-all bg-white border-slate-100 overflow-hidden`}>
                    <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${moodColor}`}/>
                    
                    <div className="flex justify-between items-start mb-3 pl-3">
                        <div className="flex flex-col">
                            <span className="text-xl font-black text-slate-800 font-mono tracking-tight">{log.date}</span>
                            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">{new Date(log.date).toLocaleDateString('en-US', {weekday:'long'})}</span>
                        </div>
                        
                        <div className="flex flex-col items-end gap-1">
                            <div className="flex gap-1">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 bg-indigo-50 text-indigo-600`}><Activity size={10}/> {m}</span>
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 bg-rose-50 text-rose-600"><Zap size={10}/> {log.metrics?.focus}</span>
                            </div>
                            <div className="flex gap-1">
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 bg-amber-50 text-amber-600"><TrendingUp size={10}/> {log.metrics?.energy}</span>
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 bg-blue-50 text-blue-600"><Clock size={10}/> {log.metrics?.deepWork}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="text-sm text-slate-600 font-sans leading-relaxed line-clamp-2 mb-3 pl-3 pr-1">
                        {log.sections?.summary || getPreviewText(log.note)}
                    </div>

                    <div className="pl-3 flex flex-col gap-2">
                        {isDrift && (
                            <div className="p-2 bg-slate-900 text-white rounded-lg text-xs font-mono flex items-center gap-2 shadow-sm w-fit">
                                <AlertTriangle size={12} className="text-amber-400"/>
                                <span className="truncate max-w-[200px]">{insight.text}</span>
                            </div>
                        )}
                        {activeHabits.length > 0 && (
                            <div className="flex gap-2 mt-1">
                                {activeHabits.map(h => {
                                    const habitConfig = config.habits.find(ch => ch.id === h);
                                    if(!habitConfig) return null;
                                    const Icon = CoreEngine.getIconComponent(habitConfig.icon);
                                    return <div key={h} className="text-slate-400 bg-slate-50 p-1 rounded-md"><Icon size={12}/></div>
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

    const renderSettingsView = () => (
        <div className="space-y-6 pb-24 animate-fade-in">
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
                 <h3 className="text-base font-bold text-slate-700 mb-2 flex items-center gap-2"><Terminal className="w-4 h-4 text-indigo-500"/> System Prompts</h3>
                 {[ {l:'Monthly',k:'monthly'}, {l:'Daily',k:'daily'} ].map(p => (
                    <div key={p.k} className="mb-4">
                        <div className="flex justify-between items-center mb-1"><label className="text-xs font-bold text-slate-500 uppercase">{p.l}</label><button onClick={() => { copyToClipboard(prompts[p.k]); showToast("📋 已複製"); }} className="text-[10px] bg-slate-100 px-2 py-1 rounded flex gap-1"><Copy className="w-3 h-3"/> 複製</button></div>
                        <textarea value={prompts[p.k] || ''} onChange={(e) => setPrompts({...prompts, [p.k]:e.target.value})} className="w-full h-24 bg-slate-50 border border-slate-200 rounded-xl p-3 text-[10px] font-mono resize-none outline-none" />
                    </div>
                 ))}
            </div>
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
                <h3 className="text-base font-bold text-slate-700 mb-2 flex items-center gap-2"><Sliders className="w-4 h-4 text-indigo-500"/> Habits</h3>
                <div className="flex gap-2 mb-4">
                    <input type="text" placeholder="新增習慣..." value={newHabitName} onChange={(e) => setNewHabitName(e.target.value)} className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none" />
                    <button onClick={addNewHabit} className="bg-indigo-600 text-white px-4 rounded-lg text-xs font-bold flex items-center gap-1"><PlusCircle className="w-3 h-3"/> 新增</button>
                </div>
                <div className="grid grid-cols-1 gap-2">
                    {config.habits.map(h => (
                        <div key={h.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                            <div className="flex items-center gap-3"><div className={`w-8 h-8 rounded-full flex items-center justify-center ${h.active?'bg-slate-800 text-white':'bg-slate-200 text-slate-400'}`}>{React.createElement(CoreEngine.getIconComponent(h.icon), { size: 14 })}</div><span className={`text-sm font-medium ${h.active?'text-slate-700':'text-slate-400 line-through'}`}>{h.label}</span></div>
                            <button onClick={() => toggleHabit(h.id)} className={`px-3 py-1 rounded-lg text-xs font-bold flex items-center gap-1 ${h.active?'bg-red-50 text-red-500':'bg-emerald-50 text-emerald-600'}`}>{h.active?<><StopCircle className="w-3 h-3"/> 停用</>:<><PlayCircle className="w-3 h-3"/> 啟用</>}</button>
                        </div>
                    ))}
                </div>
            </div>
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 space-y-3">
                <h3 className="text-base font-bold text-slate-700 mb-2 flex items-center gap-2"><Settings className="w-4 h-4 text-indigo-500"/> Data</h3>
                <div className="flex gap-2">
                    <button onClick={handleExport} className="flex-1 py-3 bg-indigo-50 text-indigo-600 rounded-xl text-xs font-bold flex justify-center items-center gap-2"><Download className="w-4 h-4"/> Backup</button>
                    <label className="flex-1 py-3 bg-emerald-50 text-emerald-600 rounded-xl text-xs font-bold flex justify-center items-center gap-2 cursor-pointer"><Upload className="w-4 h-4"/> Restore
                        <input type="file" className="hidden" onChange={handleImport}/>
                    </label>
                </div>
                <button onClick={requestClear} className="w-full py-3 bg-red-50 text-red-500 rounded-xl text-xs font-bold flex justify-center items-center gap-2"><Trash2 className="w-4 h-4"/> Clear All Data</button>
            </div>
        </div>
    );

    return (
        <div className="max-w-md mx-auto h-screen bg-slate-50 flex flex-col font-sans text-slate-900 relative shadow-2xl overflow-hidden">
            <ConfirmModal isOpen={confirmState.isOpen} title={confirmState.title} message={confirmState.message} onConfirm={confirmState.action} onCancel={() => setConfirmState({ ...confirmState, isOpen: false })} />
            
            {selectedEntry && (
                <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in" onClick={() => setSelectedEntry(null)}>
                    <div className="w-full max-w-lg max-h-[85vh] rounded-3xl shadow-2xl overflow-hidden flex flex-col animate-scale-in bg-white" onClick={e=>e.stopPropagation()}>
                        
                        <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-white/95 backdrop-blur sticky top-0 z-10">
                            <div className="flex flex-col">
                                <h3 className="font-black text-2xl text-slate-800 tracking-tight">{selectedEntry.date}</h3>
                                {/* [Cluster Fix] Show simple type if no date */}
                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                                    {selectedEntry.isStub ? 'Virtual Node' : new Date(selectedEntry.date).toLocaleDateString('en-US', {weekday:'long', month:'short'})}
                                </span>
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => {copyToClipboard(selectedEntry.note); showToast("Copied")}} className="p-2 bg-slate-50 hover:bg-slate-100 rounded-full text-slate-400 transition-all"><Clipboard size={18}/></button>
                                <button onClick={() => requestDelete(selectedEntry.date)} className="p-2 bg-red-50 hover:bg-red-100 text-red-500 rounded-full transition-all"><Trash2 size={18}/></button>
                                <button onClick={() => setSelectedEntry(null)} className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-500 rounded-full transition-all"><X size={18}/></button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar p-0">
                            <div className={`h-1.5 w-full ${selectedEntry.metrics.mood > 7 ? 'bg-gradient-to-r from-emerald-400 to-teal-500' : selectedEntry.metrics.mood < 4 ? 'bg-gradient-to-r from-rose-400 to-red-500' : 'bg-gradient-to-r from-indigo-400 to-purple-500'}`} />

                            {selectedEntry.sections?.summary && (
                                <div className="mx-5 mt-5 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                                    <div className="flex items-center gap-2 mb-2 text-slate-400">
                                        <Quote size={12} className="fill-current"/>
                                        <span className="text-[10px] font-bold uppercase tracking-widest">Day Summary</span>
                                    </div>
                                    <p className="text-sm font-medium text-slate-700 leading-relaxed italic">
                                        "{selectedEntry.sections.summary}"
                                    </p>
                                </div>
                            )}

                            <div className="mx-5 mt-4 grid grid-cols-4 gap-2">
                                {[
                                    {l:'Mood', v:selectedEntry.metrics.mood, c:'indigo', i:Activity},
                                    {l:'Focus', v:selectedEntry.metrics.focus, c:'rose', i:Zap},
                                    {l:'Energy', v:selectedEntry.metrics.energy, c:'amber', i:TrendingUp},
                                    {l:'Deep', v:`${selectedEntry.metrics.deepWork}m`, c:'blue', i:Clock},
                                ].map(m => (
                                    <div key={m.l} className={`bg-${m.c}-50 rounded-xl p-2 flex flex-col items-center justify-center border border-${m.c}-100`}>
                                        <m.i size={12} className={`text-${m.c}-500 mb-1`}/>
                                        <span className={`text-lg font-black text-${m.c}-700`}>{m.v}</span>
                                    </div>
                                ))}
                            </div>

                            <div className="p-6">
                                <MarkdownRenderer content={selectedEntry.note} />
                            </div>
                            
                            <div className="px-6 pb-8">
                                <span className="text-[10px] font-bold text-slate-300 block mb-3 uppercase tracking-widest">Completed Habits</span>
                                <div className="flex flex-wrap gap-2">
                                    {Object.keys(selectedEntry.habits).filter(h => selectedEntry.habits[h]).map(h => {
                                        const cfg = config.habits.find(c => c.id === h);
                                        if(!cfg) return null;
                                        const Icon = CoreEngine.getIconComponent(cfg.icon);
                                        return <span key={h} className="px-3 py-1.5 bg-white border border-slate-100 text-slate-600 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-sm"><Icon size={12}/>{cfg.label}</span>
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <ContextModal 
                mainNode={contextNode} 
                logs={logs} 
                onClose={() => setContextNode(null)} 
                onOpenEntry={(entry) => { 
                    setSelectedEntry(entry); 
                }} 
            />

            {notification && (
                <div className={`fixed top-6 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-full text-xs font-bold shadow-xl z-[100] flex items-center gap-2 animate-fade-in-up ${notification.type==='error'?'bg-red-500 text-white':'bg-slate-800 text-white'}`}>
                    {notification.type==='error'?<AlertTriangle size={14}/>:<Check size={14}/>} {notification.msg}
                </div>
            )}

            <header className="px-6 py-4 bg-white/90 backdrop-blur z-20 flex justify-between items-center border-b border-slate-200/50 sticky top-0">
                <div><h1 className="text-lg font-black tracking-tight text-slate-900">LifeOS <span className="text-indigo-600 text-xs align-top">v{VERSION}</span></h1></div>
                <div className="w-8 h-8 rounded-full bg-indigo-100 overflow-hidden"><img src={userSettings?.avatar || DEFAULT_SETTINGS.avatar} className="w-full h-full object-cover"/></div>
            </header>

            <main className="flex-1 overflow-y-auto p-4 scroll-smooth">
                {activeTab === 'input' && renderInputTab()}
                {activeTab === 'graph' && (
                    <div className="space-y-4 animate-fade-in h-full flex flex-col">
                        <div className="bg-white p-4 rounded-3xl shadow-sm border border-slate-100 flex-1 flex flex-col">
                            <h3 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2"><Network className="w-4 h-4 text-indigo-500"/> 無限圖譜 (Infinite Graph)</h3>
                            {/* [D3 Integrated Component] */}
                            <NeuralGraph logs={logs} onNodeClick={setContextNode} />
                            
                            <p className="text-center text-[10px] text-slate-400 mt-2">滾輪縮放 (Zoom) • 拖曳移動 (Drag) • 點擊節點 (Context)</p>
                        </div>
                    </div>
                )}
                {activeTab === 'dashboard' && renderDashboard()}
                {activeTab === 'history' && renderHistoryView()}
                {activeTab === 'settings' && renderSettingsView()}
            </main>

            <nav className="bg-white border-t border-slate-200 p-2 flex justify-around items-center z-30 pb-safe">
                {[
                    {id:'input', icon:Edit3, label:'Log'},
                    {id:'graph', icon:Network, label:'Graph'},
                    {id:'dashboard', icon:Activity, label:'Dash'},
                    {id:'history', icon:Footprints, label:'Foot'},
                    {id:'settings', icon:Settings, label:'Sys'}
                ].map(tab => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all w-16 ${activeTab === tab.id ? 'text-indigo-600 bg-indigo-50' : 'text-slate-400 hover:bg-slate-50'}`}>
                        {React.createElement(tab.icon, { size: 20, className: activeTab === tab.id ? 'stroke-[2.5px]' : 'stroke-2' })}
                        <span className="text-[10px] font-bold">{tab.label}</span>
                    </button>
                ))}
            </nav>
        </div>
    );
};

export default LifeOS;       