import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeMode = 'dark' | 'light';

export interface Habit {
    id: string;
    label: string;
    icon: string;
    active: boolean;
}

interface SettingsState {
    theme: ThemeMode;
    prompts: string[];
    habits: Habit[]; // Changed to object array for icon/label support
    apiKeys: Record<string, string>; // [NEW] API Keys
    toggleTheme: () => void;
    addPrompt: (prompt: string) => void;
    removePrompt: (index: number) => void;
    addHabit: (habit: string) => void; // Simplified for UI
    removeHabit: (index: number) => void;
    setApiKey: (key: string, value: string) => void; // [NEW]
    resetDefaults: () => void;
}

const DEFAULT_PROMPTS = [
    "What was the highlight of today?",
    "What did I learn?",
    "How can I improve tomorrow?"
];

const DEFAULT_HABITS_LIST: Habit[] = [
    { id: 'deep_work', label: 'Deep Work', icon: 'Rocket', active: true },
    { id: 'sleep_7h', label: 'Sleep 7h+', icon: 'Moon', active: true },
    { id: 'read', label: 'Read', icon: 'BookOpen', active: true },
    { id: 'exercise', label: 'Exercise', icon: 'Activity', active: true },
    { id: 'meditation', label: 'Meditation', icon: 'Brain', active: true }
];

export const useSettings = create<SettingsState>()(
    persist(
        (set) => ({
            theme: 'dark',
            prompts: DEFAULT_PROMPTS,
            habits: DEFAULT_HABITS_LIST,
            apiKeys: {}, // Init
            toggleTheme: () => set((state: SettingsState) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
            addPrompt: (prompt) => set((state: SettingsState) => ({ prompts: [...state.prompts, prompt] })),
            removePrompt: (index) => set((state: SettingsState) => ({ prompts: state.prompts.filter((_, i) => i !== index) })),
            addHabit: (habitLabel) => set((state: SettingsState) => {
                // Simple ID generation
                const id = habitLabel.toLowerCase().replace(/\s+/g, '_');
                const newHabit: Habit = { id, label: habitLabel, icon: 'Star', active: true };
                return { habits: [...state.habits, newHabit] };
            }),
            removeHabit: (index) => set((state: SettingsState) => ({ habits: state.habits.filter((_, i) => i !== index) })),
            setApiKey: (key, value) => set((state: SettingsState) => ({ apiKeys: { ...state.apiKeys, [key]: value } })),
            resetDefaults: () => set({ prompts: DEFAULT_PROMPTS, habits: DEFAULT_HABITS_LIST })
        }),
        {
            name: 'life-os-settings-storage',
        }
    )
);
