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
        
        // [Fix] 改用 Array.from 以相容舊版 TS 設定
        return { 
            tags: Array.from(new Set(tags)), 
            links: Array.from(new Set(links)) 
        };
    }
};
