'use client';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, RefreshCw, Key, Box, Shield, Zap, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { useSettings } from '@/lib/hooks/useSettings';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

type Tab = 'general' | 'integrations' | 'developer';

export const SettingsModal = ({ isOpen, onClose }: SettingsModalProps) => {
    const [activeTab, setActiveTab] = useState<Tab>('integrations');
    const { apiKeys, setApiKey, resetDefaults } = useSettings();

    // Helper for API Input
    const APIInput = ({ label, skey, placeholder }: { label: string, skey: string, placeholder: string }) => {
        const isConnected = !!apiKeys[skey] && apiKeys[skey].length > 10;

        return (
            <div className="space-y-2">
                <div className="flex justify-between items-center">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        {label}
                        {isConnected ? (
                            <span className="text-[10px] text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Connected
                            </span>
                        ) : (
                            <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">Not Configured</span>
                        )}
                    </label>
                </div>
                <div className="relative group">
                    <input
                        type="password"
                        value={apiKeys[skey] || ''}
                        onChange={(e) => setApiKey(skey, e.target.value)}
                        placeholder={placeholder}
                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:ring-1 focus:ring-indigo-500/50 outline-none font-mono tracking-tighter transition-all group-hover:border-white/20"
                    />
                    <Key size={14} className="absolute right-4 top-3.5 text-slate-600 group-focus-within:text-indigo-500 transition-colors" />
                </div>
            </div>
        );
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-4xl h-[80vh] bg-[#0f172a] rounded-3xl shadow-2xl overflow-hidden flex flex-col md:flex-row border border-slate-800 animate-in zoom-in-95 duration-200">

                {/* Sidebar */}
                <aside className="w-full md:w-64 bg-slate-900/50 p-6 flex flex-col border-r border-slate-800/50">
                    <div className="mb-8 flex items-center gap-3 text-white">
                        <div className="p-2 bg-indigo-500 rounded-lg">
                            <Settings size={20} className="text-white" />
                        </div>
                        <div>
                            <h2 className="font-bold text-lg leading-tight">System Core</h2>
                            <p className="text-xs text-slate-500">v3.1 Configuration</p>
                        </div>
                    </div>

                    <nav className="flex-1 space-y-1">
                        {[
                            { id: 'general', label: 'General', icon: Box },
                            { id: 'integrations', label: 'Integrations', icon: Zap },
                            { id: 'developer', label: 'Developer', icon: Shield },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as Tab)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === tab.id
                                        ? 'bg-indigo-500/10 text-indigo-400'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                                    }`}
                            >
                                <tab.icon size={16} />
                                {tab.label}
                            </button>
                        ))}
                    </nav>

                    <button onClick={onClose} className="mt-auto flex items-center gap-2 text-slate-500 hover:text-white transition-colors px-4 py-2">
                        <X size={16} /> Close Settings
                    </button>
                </aside>

                {/* Main Content */}
                <main className="flex-1 overflow-y-auto p-8 custom-scrollbar bg-[#0f172a] relative">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.2 }}
                        >
                            {activeTab === 'integrations' && (
                                <div className="space-y-8">
                                    <header>
                                        <h3 className="text-2xl font-bold text-white mb-2">Integrations</h3>
                                        <p className="text-slate-400 text-sm">Manage connection keys for external neural links.</p>
                                    </header>

                                    <div className="grid grid-cols-1 gap-6 max-w-2xl">
                                        <section className="bg-slate-900/50 rounded-2xl p-6 border border-slate-800">
                                            <h4 className="text-sm font-bold text-indigo-400 mb-4 uppercase tracking-wider flex items-center gap-2">
                                                <Zap size={14} /> AI Services
                                            </h4>
                                            <div className="space-y-6">
                                                <APIInput label="OpenAI API Key" skey="openai" placeholder="sk-..." />
                                                <APIInput label="Anthropic API Key" skey="anthropic" placeholder="sk-ant-..." />
                                            </div>
                                        </section>

                                        <section className="bg-slate-900/50 rounded-2xl p-6 border border-slate-800">
                                            <h4 className="text-sm font-bold text-emerald-400 mb-4 uppercase tracking-wider flex items-center gap-2">
                                                <Box size={14} /> Database & Storage
                                            </h4>
                                            <div className="space-y-6">
                                                <APIInput label="Supabase URL" skey="supabase_url" placeholder="https://..." />
                                                <APIInput label="Supabase Anon Key" skey="supabase_key" placeholder="eyJ..." />
                                            </div>
                                        </section>

                                        <section className="bg-slate-900/50 rounded-2xl p-6 border border-slate-800">
                                            <h4 className="text-sm font-bold text-pink-400 mb-4 uppercase tracking-wider flex items-center gap-2">
                                                <AlertCircle size={14} /> Webhooks
                                            </h4>
                                            <div className="space-y-6">
                                                <APIInput label="Discord Webhook" skey="discord_webhook" placeholder="https://discord.com/api/webhooks/..." />
                                                <APIInput label="Google Tasks JSON" skey="google_tasks_json" placeholder="{ type: service_account ... }" />
                                            </div>
                                        </section>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'general' && (
                                <div className="space-y-8">
                                    <header>
                                        <h3 className="text-2xl font-bold text-white mb-2">General Settings</h3>
                                        <p className="text-slate-400 text-sm">Configure base system parameters.</p>
                                    </header>
                                    <div className="p-12 text-center border-2 border-dashed border-slate-800 rounded-2xl">
                                        <p className="text-slate-500">Prompts & Habits configuration is managed in standard view.</p>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'developer' && (
                                <div className="space-y-8">
                                    <header>
                                        <h3 className="text-2xl font-bold text-white mb-2">Developer Zone</h3>
                                        <p className="text-slate-400 text-sm">Advanced system controls.</p>
                                    </header>

                                    <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-6">
                                        <h4 className="text-red-400 font-bold mb-2 flex items-center gap-2">
                                            <AlertCircle size={16} /> Danger Zone
                                        </h4>
                                        <p className="text-slate-500 text-sm mb-4">Resetting defaults will clear all local configuration.</p>
                                        <button
                                            onClick={() => { if (confirm('Factory Reset?')) resetDefaults(); }}
                                            className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg text-sm font-bold transition-colors flex items-center gap-2"
                                        >
                                            <RefreshCw size={14} /> Factory Reset
                                        </button>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    </AnimatePresence>
                </main>
            </div>
        </div>
    );
};
