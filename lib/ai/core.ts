// lib/ai/core.ts

import { LucideIcon, Zap, BookOpen, Dumbbell, Code, Layout, Calendar, CheckCircle } from 'lucide-react';

/**
 * Neon Palette for D3 Graph
 */
export const NEON_PALETTE = {
    INDIGO: "#818cf8",  // Default Node
    EMERALD: "#34d399", // High Mood
    ROSE: "#fb7185",    // Low Mood
    AMBER: "#fbbf24",   // Warning / High Energy
    CYAN: "#22d3ee",    // Tech / Code
    PINK: "#f472b6",    // Tags
    SLATE: "#94a3b8",    // Inactive
    BLUE: "#3b82f6"
};

export const DEFAULT_HABITS = [
    { id: 'h1', label: 'Deep Work', icon: '⚡' },
    { id: 'h2', label: 'Workout', icon: '💪' },
    { id: 'h3', label: 'Reading', icon: '📚' },
    { id: 'h4', label: 'Coding', icon: '💻' }
];

export class CoreEngine {
    /**
     * 從原始筆記中提取標籤 (#tag) 與連結 ([link])
     * 這是建立知識圖譜的關鍵步驟
     */
    static parseGraphSeeds(rawText: string, aiContent?: any) {
        const tags = new Set<string>();
        const links = new Set<string>();

        // 1. Regex 解析 Hashtags (#React, #Life)
        const tagRegex = /#([\w\u4e00-\u9fa5]+)/g;
        let match;
        while ((match = tagRegex.exec(rawText)) !== null) {
            tags.add(match[1]);
        }

        // 2. Regex 解析 Wiki Links ([[ProjectA]])
        const linkRegex = /\[\[(.*?)\]\]/g;
        while ((match = linkRegex.exec(rawText)) !== null) {
            links.add(match[1]);
        }
        
        // 3. 整合 AI 分析的結果 (如果有)
        if (aiContent?.tags) {
            aiContent.tags.forEach((t: string) => tags.add(t));
        }

        return {
            tags: Array.from(tags),
            links: Array.from(links)
        };
    }

    /**
     * 計算節點的物理權重 (由 Metrics 決定)
     */
    static calculateNodeWeight(metrics: any) {
        // 基礎大小 10 + 專注度加權
        return 10 + (metrics?.focus || 0) * 1.5;
    }

    /**
     * 從文本中提取待辦事項 (- [ ] task)
     */
    static extractTasks(text: string): string[] {
        const taskRegex = /- \[ \] (.*)/g;
        const tasks: string[] = [];
        let match;
        while ((match = taskRegex.exec(text)) !== null) {
            tasks.push(match[1]);
        }
        return tasks;
    }

    /**
     * 提取簡短摘要或洞察
     */
    static extractInsight(text: string): { type: 'normal' | 'drift', text: string } {
        // 簡單邏輯：如果過短，視為 drift (這裡僅為範例)
        if (text.length < 10) {
            return { type: 'drift', text: 'Low information density' };
        }
        return { type: 'normal', text: text.substring(0, 50) + (text.length > 50 ? '...' : '') };
    }

    /**
     * 獲取 Icon 組件
     */
    static getIconComponent(iconStr: string): LucideIcon {
        // 簡單映射，實際專案可能需要更完整的映射表
        switch (iconStr) {
            case '⚡': return Zap;
            case '💪': return Dumbbell;
            case '📚': return BookOpen;
            case '💻': return Code;
            default: return CheckCircle;
        }
    }
}