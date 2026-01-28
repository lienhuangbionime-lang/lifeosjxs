import { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal } from 'lucide-react';

export const VERSION = "10.3 (Cloud Agent)"; 

export const NEON_PALETTE = {
    EMERALD: '#10b981', ROSE: '#f43f5e', BLUE: '#3b82f6', 
    INDIGO: '#6366f1', SLATE: '#475569', AMBER: '#f59e0b', PINK: '#ec4899'
};

export const DEFAULT_HABITS = [
    { id: 'reading', label: '閱讀 Input', icon: 'BookOpen', active: true },
    { id: 'native_coding', label: 'Native Logic', icon: 'Terminal', active: true },
    { id: 'creation', label: '創作 Output', icon: 'Zap', active: true },
    { id: 'exercise', label: '運動 Health', icon: 'Activity', active: true },
    { id: 'meditation', label: '反思 Meta', icon: 'Brain', active: true }
];

export class CoreEngine {
    // 加入 'static' 關鍵字
    static getIconComponent(iconName: string) {
        const map: any = { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal };
        return map[iconName] || Star; 
    }
    
    // 加入 'static' 關鍵字
    static sanitizeLogEntry(entry: any) {
        return {
            ...entry,
            date: entry.date || new Date().toISOString().split('T')[0],
            metrics: { 
                mood: Number(entry.metrics?.mood || 5), 
                focus: Number(entry.metrics?.focus || 5), 
                energy: Number(entry.metrics?.energy || 5),
                deepWork: Number(entry.metrics?.deepWork || 0)
            },
            graphSeeds: {
                tags: entry.graphSeeds?.tags || '',
                links: entry.graphSeeds?.links || '',
                content: entry.graphSeeds?.content || ''
            }
        };
    }

    // 加入 'static' 關鍵字
    static extractInsight(content: string) {
        if (!content) return { type: 'empty', text: '無文字紀錄' };
        if (content.includes('Core Weakness')) return { type: 'bias', text: 'Core Weakness Detected', label: 'Bias' };
        const lines = content.split('\n');
        const preview = lines.find(l => l.length > 5 && !l.startsWith('#') && !l.startsWith('>')) || '無詳細內容';
        return { type: 'general', text: preview.slice(0, 60), label: 'Log' };
    }

    // 加入 'static' 關鍵字
    static parseGraphSeeds(note: string, graphContent = '') {
        if (!note) return { tags: [], links: [] };
        const combined = note + ' ' + graphContent;
        const tags = (combined.match(/#([\w\u4e00-\u9fa5]+)/g) || []).map(t => t.slice(1));
        const links = (combined.match(/\[\[(\d{4}-\d{2}-\d{2})\]\]/g) || []).map(l => l.slice(2, -2));
        return { tags: [...new Set(tags)], links: [...new Set(links)] };
    }
}