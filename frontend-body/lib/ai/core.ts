// 檔案位置: lib/ai/core.ts
import { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal } from 'lucide-react';

// [核心設定]
// [核心設定]
export const DEFAULT_HABITS = [
    { id: 'reading', label: '閱讀 Input', icon: 'BookOpen', active: true },
    { id: 'native_coding', label: 'Native Logic', icon: 'Terminal', active: true },
    { id: 'creation', label: '創作 Output', icon: 'Zap', active: true },
    { id: 'exercise', label: '運動 Health', icon: 'Activity', active: true },
    { id: 'meditation', label: '反思 Meta', icon: 'Brain', active: true }
];

export const NEON_PALETTE = {
    EMERALD: '#10b981', // High Mood / Flow
    ROSE: '#f43f5e',    // Low Mood / Warning
    BLUE: '#3b82f6',    // Deep Work / Signal
    INDIGO: '#6366f1',  // Neutral
    SLATE: '#475569',   // Noise / Background
    AMBER: '#f59e0b',   // Project / Drift
    PINK: '#ec4899',    // Tags
    GLOW_COLOR: '#ffffff'
};

const BIAS_KEYWORDS = ['確認偏誤', '沉沒成本', '過擬合', '爆倉', '手癢', 'App 替代陪伴', 'Core Weakness', '逃避'];

export const CoreEngine = {
    getIconComponent: (iconName: string) => {
        const map: any = { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal };
        return map[iconName] || Star;
    },

    // [White Screen Fix] Factory for virtual nodes
    generateStubLog: (id: string, group: string) => {
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

    sanitizeLogEntry: (entry: any, index: number = 0) => {
        const safeDate = entry.date || `1970-01-01_${index}`;

        let summary = entry.sections?.summary || '';
        // Extract summary from note if missing
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

    sanitizeData: (rawData: any[]) => {
        if (!Array.isArray(rawData)) return [];
        return rawData
            .filter(item => item && typeof item === 'object')
            .map((item, idx) => CoreEngine.sanitizeLogEntry(item, idx))
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    },

    extractInsight: (content: string) => {
        if (!content) return { type: 'empty', text: '無文字紀錄', label: 'Empty' };

        const foundBias = BIAS_KEYWORDS.find(k => content.includes(k));
        if (foundBias) {
            const sentences = content.split(/[。\n]/);
            const targetSentence = sentences.find(s => s.includes(foundBias)) || foundBias;
            return { type: 'bias', text: targetSentence.trim().slice(0, 60), label: '⚠️ Bias' };
        }

        const driftMatch = content.match(/(?:Drift Point|偏移點|Drift)[^:\n]*[:：]?\s*(.*)/i);
        if (driftMatch && driftMatch[1] && driftMatch[1].trim() !== 'None') {
            return { type: 'drift', text: driftMatch[1].replace(/\*\*/g, '').trim(), label: '⚠️ Drift' };
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
        return { type: 'general', text: finalText.slice(0, 80) + (finalText.length > 80 ? '...' : ''), label: '📄 Log' };
    },

    // [Task Bridge] Extract TODOs
    extractTasks: (content: string) => {
        if (!content) return [];
        const regex = /(?:- \[ \]|TODO|URGENT|待辦|\[ \])\s*(.*)/gi;
        const tasks: string[] = [];
        let match;
        while ((match = regex.exec(content)) !== null) {
            if (match[1] && match[1].trim()) {
                tasks.push(match[1].trim());
            }
        }
        return tasks;
    },

    parseGraphSeeds: (note: string, graphContent = '') => {
        if (!note || typeof note !== 'string') return { tags: [], links: [] };
        const combinedText = note + ' ' + graphContent;
        const tags = (combinedText.match(/#([\w\u4e00-\u9fa5]+)/g) || []).map(t => t.slice(1)).filter(t => !BIAS_KEYWORDS.includes(t));
        const links = (combinedText.match(/\[\[(\d{4}-\d{2}-\d{2})\]\]/g) || []).map(l => l.slice(2, -2));

        // [Fix] Array.from used for robustness
        return {
            tags: Array.from(new Set(tags)),
            links: Array.from(new Set(links))
        };
    }
};
