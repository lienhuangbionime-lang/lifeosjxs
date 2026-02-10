import { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal, Moon } from 'lucide-react';
import type { SimulationNodeDatum } from 'd3';

// --- Type Definitions ---
export interface LogEntry {
    id?: number;
    date: string;
    note: string;
    metrics: { count?: number; mood?: number; focus?: number; energy?: number };
    habits: Record<string, boolean>;
    graphSeeds?: { tags: string; links: string; content?: string };
    tags?: string[];
}

export interface Insight {
    type: 'trend' | 'pattern' | 'alert';
    content: string;
    confidence: number;
}

export interface Task {
    id: string;
    content: string;
    status: 'pending' | 'completed';
}

export interface GraphNode extends SimulationNodeDatum {
    id: string;
    group: number | string; // 1=Log, 2=Tag or 'tag'
    val?: number; // for D3
    raw?: LogEntry; // Link back to source
    // D3 Simulation Props (optional but needed for TS)
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;
}

export interface GraphLink {
    source: string;
    target: string;
    value?: number;
}

export interface GraphData {
    nodes: GraphNode[];
    links: GraphLink[];
}

// --- Constants ---
export const NEON_PALETTE = {
    primary: '#00ff9d',   // Neon Green (Lime-ish)
    secondary: '#00d2ff', // Neon Blue (Cyan)
    accent: '#d946ef',    // Neon Pink (Fuchsia)
    violet: '#8b5cf6',    // Neon Violet
    alert: '#ff0055',     // Neon Red
    warning: '#ffcc00',   // Neon Yellow
    bg: '#0a0a0a',        // Deep Black

    // User Requested Exact Palette Mapping
    NEON_PINK: '#ff00ff',
    NEON_CYAN: '#00ffff',
    NEON_LIME: '#ccff00',
    NEON_VIOLET: '#9d00ff',

    // Legacy Support
    EMERALD: '#00ff9d',
    ROSE: '#ff0055',
    BLUE: '#00d2ff',
    AMBER: '#ffcc00',
    SLATE: '#475569',
    PINK: '#ec4899'
};

export const DEFAULT_HABITS = [
    { id: 'deep_work', label: 'Deep Work', icon: 'Rocket', active: true },
    { id: 'sleep_7h', label: 'Sleep 7h+', icon: 'Moon', active: true },
    { id: 'read', label: 'Read', icon: 'BookOpen', active: true },
    { id: 'exercise', label: 'Exercise', icon: 'Activity', active: true },
    { id: 'meditation', label: 'Meditation', icon: 'Brain', active: true }
];

// --- Core Engine ---
export const CoreEngine = {
    getIconComponent: (iconName: string) => {
        const map: any = { BookOpen, Activity, Zap, Brain, Star, TrendingUp, Target, Heart, Rocket, Terminal, Moon };
        return map[iconName] || Star;
    },

    sanitizeLogEntry: (raw: string): string => {
        if (!raw) return '';
        return raw.trim()
            .replace(/\r\n/g, '\n')
            .replace(/\n{3,}/g, '\n\n'); // Max 2 newlines
    },

    extractInsight: (log: LogEntry | string): string => {
        const text = typeof log === 'string' ? log : log.note;
        if (!text) return "No data";

        // Heuristic: Check for explicit insight markers
        const insightMatch = text.match(/(?:#insight|💡)\s*(.*)/i);
        if (insightMatch && insightMatch[1]) return insightMatch[1].trim();

        if (typeof log === 'string') return "Keep logging to generate insights.";

        const mood = log.metrics?.mood || 5;
        const tags = log.tags || [];

        if (mood >= 8) return "High energy detected! Capitalize on this flow state.";
        if (mood <= 3) return "Energy low. Consider a restorative break.";
        if (tags.includes('code')) return "Coding focus active. Keep shipping.";
        if (tags.includes('read')) return "Knowledge intake mode.";

        return "Steady progress. Keep logging.";
    },

    extractTasks: (log_content: string): Task[] => {
        if (!log_content) return [];
        // Regex for "- [ ]" or "[ ]" or "TODO:"
        const regex = /^(?:-?\s*\[\s*\]|TODO:|URGENT:)\s*(.*)/gim;
        const tasks: Task[] = [];
        let match;
        while ((match = regex.exec(log_content)) !== null) {
            if (match[1] && match[1].trim()) {
                tasks.push({
                    id: Math.random().toString(36).substr(2, 9),
                    content: match[1].trim(),
                    status: 'pending'
                });
            }
        }
        return tasks;
    },

    parseNoteSeeds: (content: string): { tags: string[], links: string[] } => {
        if (!content) return { tags: [], links: [] };
        const foundTags = (content.match(/#([\w\u4e00-\u9fa5]+)/g) || []).map(t => t.slice(1));
        const uniqueTags = Array.from(new Set(foundTags));
        // Simple link extraction if [[Link]] format is used, or just return empty for now if not implemented
        // For now, let's assume links are also tags or just empty. 
        // If the legacy code expected links, maybe it regexes for [[...]]? 
        // The error shows 'links' being accessed.
        return { tags: uniqueTags, links: [] };
    },

    parseGraphSeeds: (logs: LogEntry[]): GraphData => {
        const nodes = new Map<string, GraphNode>();
        const linkMap = new Map<string, GraphLink>();

        logs.forEach(log => {
            // 1. Create Log Node
            // Use log.date as ID, but maybe append a prefix if ID conflict is possible?
            // For now assuming date is unique enough for the log node ID.
            if (!nodes.has(log.date)) {
                nodes.set(log.date, {
                    id: log.date,
                    group: 1,
                    val: 5,
                    raw: log
                });
            }

            // Combine all content sources
            const content = (log.note || '') + '\n' + (log.graphSeeds?.content || '');

            // 2. Extract Tags (#tag) - allow dots/dashes
            const tagMatches = content.match(/#([\w\u4e00-\u9fa5.-]+)/g) || [];
            let tags = Array.from(new Set(tagMatches.map(t => t.slice(1))));

            // [FIX] Also include explicit tags from DB
            if (log.tags && Array.isArray(log.tags)) {
                const dbTags = log.tags.map(t => t.replace(/^#/, ''));
                tags = Array.from(new Set([...tags, ...dbTags]));
            }

            // 3. Extract Wiki Links ([[Link]])
            const linkMatches = content.match(/\[\[(.*?)\]\]/g) || [];
            const wikiLinks = Array.from(new Set(linkMatches.map(l => l.slice(2, -2))));

            // 3.1 Extract Mentions (@Name)
            const mentionMatches = content.match(/@([\w\u4e00-\u9fa5.-]+)/g) || [];
            const mentions = Array.from(new Set(mentionMatches.map(m => m.slice(1))));

            // Process Tags
            tags.forEach(tag => {
                if (!nodes.has(tag)) {
                    nodes.set(tag, { id: tag, group: 'tag', val: 3 });
                }

                // Link: Log -> Tag
                const linkKey = `${log.date}-${tag}`;
                if (!linkMap.has(linkKey)) {
                    linkMap.set(linkKey, { source: log.date, target: tag, value: 1 });
                } else {
                    linkMap.get(linkKey)!.value! += 0.5;
                }
            });

            // Process Wiki Links
            wikiLinks.forEach(linkTarget => {
                const targetId = linkTarget.trim();
                if (!targetId) return;

                if (!nodes.has(targetId)) {
                    nodes.set(targetId, { id: targetId, group: 'concept', val: 4 });
                }

                const linkKey = `${log.date}-${targetId}`;
                if (!linkMap.has(linkKey)) {
                    linkMap.set(linkKey, { source: log.date, target: targetId, value: 2 });
                } else {
                    linkMap.get(linkKey)!.value! += 1;
                }
            });

            // Process Mentions
            mentions.forEach(person => {
                if (!nodes.has(person)) {
                    nodes.set(person, { id: person, group: 'person', val: 5 });
                }

                const linkKey = `${log.date}-${person}`;
                if (!linkMap.has(linkKey)) {
                    linkMap.set(linkKey, { source: log.date, target: person, value: 2 });
                } else {
                    linkMap.get(linkKey)!.value! += 1;
                }
            });

            // 4. Co-occurrence (Tag <-> Tag)
            tags.forEach((t1, i) => {
                tags.slice(i + 1).forEach(t2 => {
                    const [source, target] = [t1, t2].sort();
                    const linkKey = `${source}-${target}`;
                    if (!linkMap.has(linkKey)) {
                        linkMap.set(linkKey, { source, target, value: 0.2 }); // Weaker link
                    } else {
                        linkMap.get(linkKey)!.value! += 0.1;
                    }
                });
            });
        });

        // Convert Maps to Arrays
        const nodesArray = Array.from(nodes.values());
        const linksArray = Array.from(linkMap.values());

        return { nodes: nodesArray, links: linksArray };
    }
};
