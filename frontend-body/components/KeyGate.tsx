'use client';
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Key, Database, ExternalLink, CheckCircle, Loader2, AlertCircle } from 'lucide-react';

/**
 * [v5.4] KeyGate — Privacy Sandbox Enforcer
 *
 * Wraps the entire app. If the user hasn't entered their own API keys
 * in Settings (stored in localStorage via Zustand), they see this
 * setup wizard instead. They CANNOT access any data without their own keys.
 *
 * This prevents visitors from accidentally reading the owner's Supabase data.
 */

interface KeyGateProps {
    children: React.ReactNode;
}

function readApiKeys(): Record<string, string> {
    if (typeof window === 'undefined') return {};
    try {
        const raw = localStorage.getItem('life-os-settings-storage');
        if (!raw) return {};
        return JSON.parse(raw)?.state?.apiKeys || {};
    } catch {
        return {};
    }
}

function isConfigured(keys: Record<string, string>): boolean {
    return !!(keys.google_api_key && keys.supabase_url && keys.supabase_key);
}

export function KeyGate({ children }: KeyGateProps) {
    const [keys, setKeys] = useState<Record<string, string>>({});
    const [mounted, setMounted] = useState(false);
    const [form, setForm] = useState({ google_api_key: '', supabase_url: '', supabase_key: '' });
    const [testing, setTesting] = useState(false);
    const [testError, setTestError] = useState('');
    const [testOk, setTestOk] = useState(false);

    useEffect(() => {
        setKeys(readApiKeys());
        setMounted(true);
    }, []);

    // Not mounted yet — don't flash content
    if (!mounted) return null;

    // Already configured — render the real app
    if (isConfigured(keys)) return <>{children}</>;

    // --- Setup Wizard ---
    const handleChange = (k: string, v: string) => {
        setForm(prev => ({ ...prev, [k]: v }));
        setTestError('');
        setTestOk(false);
    };

    const handleGuest = () => {
        localStorage.setItem('life-os-guest-mode', 'true');
        setTestOk(true);
        setTimeout(() => window.location.reload(), 400);
    };

    const handleSave = async () => {
        if (!form.google_api_key || !form.supabase_url || !form.supabase_key) {
            setTestError('Please fill in all three fields.');
            return;
        }
        setTesting(true);
        setTestError('');
        setTestOk(false);

        try {
            // Quick connectivity test: hit /status endpoint with user keys
            const res = await fetch('/api/py/status', {
                headers: {
                    'X-Gemini-Key': form.google_api_key,
                    'X-Supabase-URL': form.supabase_url,
                    'X-Supabase-Key': form.supabase_key,
                },
            });

            if (!res.ok) throw new Error(`Server returned ${res.status}`);

            // Save into Zustand persist storage
            const existing = JSON.parse(localStorage.getItem('life-os-settings-storage') || '{"state":{}}');
            existing.state = existing.state || {};
            existing.state.apiKeys = {
                ...(existing.state.apiKeys || {}),
                ...form,
            };
            localStorage.setItem('life-os-settings-storage', JSON.stringify(existing));

            setTestOk(true);
            setTimeout(() => window.location.reload(), 800); // reload to enter app
        } catch (e: any) {
            setTestError(e.message || 'Connection failed. Please check your keys.');
        } finally {
            setTesting(false);
        }
    };

    // If already in guest mode but hasn't fully reloaded or something weird
    if (typeof window !== 'undefined' && localStorage.getItem('life-os-guest-mode') === 'true') {
        return <>{children}</>;
    }

    return (
        <div className="min-h-screen bg-[#080c14] flex items-center justify-center p-4">
            {/* Background glow */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-indigo-600/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] bg-violet-600/8 rounded-full blur-[100px]" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 24, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className="relative z-10 w-full max-w-md"
            >
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 mb-4">
                        <Shield className="w-8 h-8 text-indigo-400" />
                    </div>
                    <h1 className="text-2xl font-black text-white mb-2">LifeOS Setup</h1>
                    <p className="text-slate-400 text-sm leading-relaxed">
                        This is a <span className="text-indigo-400 font-semibold">private instance</span>. Enter your own API keys to create a fully isolated workspace — your data stays in your Supabase, your AI quota is yours alone.
                    </p>
                </div>

                {/* Card */}
                <div className="bg-slate-900/80 backdrop-blur-xl rounded-3xl border border-slate-700/50 p-6 shadow-2xl space-y-4">

                    {/* Gemini Key */}
                    <div className="space-y-1.5">
                        <label className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
                            <Key className="w-3 h-3 text-yellow-400" /> Google Gemini API Key
                        </label>
                        <input
                            type="password"
                            value={form.google_api_key}
                            onChange={e => handleChange('google_api_key', e.target.value)}
                            placeholder="AIza..."
                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-600 focus:ring-1 focus:ring-indigo-500/50 outline-none font-mono"
                        />
                        <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:underline">
                            Get a free key at aistudio.google.com <ExternalLink className="w-3 h-3" />
                        </a>
                    </div>

                    {/* Supabase URL */}
                    <div className="space-y-1.5">
                        <label className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
                            <Database className="w-3 h-3 text-cyan-400" /> Supabase Project URL
                        </label>
                        <input
                            type="url"
                            value={form.supabase_url}
                            onChange={e => handleChange('supabase_url', e.target.value)}
                            placeholder="https://xxxx.supabase.co"
                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-600 focus:ring-1 focus:ring-cyan-500/50 outline-none font-mono"
                        />
                    </div>

                    {/* Supabase Key */}
                    <div className="space-y-1.5">
                        <label className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
                            <Database className="w-3 h-3 text-cyan-400" /> Supabase anon / service_role Key
                        </label>
                        <input
                            type="password"
                            value={form.supabase_key}
                            onChange={e => handleChange('supabase_key', e.target.value)}
                            placeholder="eyJ..."
                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-600 focus:ring-1 focus:ring-cyan-500/50 outline-none font-mono"
                        />
                        <a href="https://supabase.com/dashboard" target="_blank" rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:underline">
                            Create a free project at supabase.com <ExternalLink className="w-3 h-3" />
                        </a>
                    </div>

                    {/* Error / Success */}
                    <AnimatePresence>
                        {testError && (
                            <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                                <AlertCircle className="w-3.5 h-3.5 shrink-0" /> {testError}
                            </motion.div>
                        )}
                        {testOk && (
                            <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
                                className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-3 py-2">
                                <CheckCircle className="w-3.5 h-3.5" /> Connected! Entering your workspace...
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Submit */}
                    <div className="space-y-3">
                        <button
                            onClick={handleSave}
                            disabled={testing || testOk}
                            className="w-full py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20"
                        >
                            {testing ? <><Loader2 className="w-4 h-4 animate-spin" /> Testing connection...</> :
                                testOk ? <><CheckCircle className="w-4 h-4" /> Launching...</> :
                                    <><Shield className="w-4 h-4" /> Connect &amp; Enter LifeOS</>}
                        </button>

                        <div className="relative flex items-center py-2">
                            <div className="flex-grow border-t border-slate-700/50"></div>
                            <span className="flex-shrink-0 mx-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">or</span>
                            <div className="flex-grow border-t border-slate-700/50"></div>
                        </div>

                        <button
                            onClick={handleGuest}
                            disabled={testing || testOk}
                            className="w-full py-3 rounded-2xl bg-transparent border border-slate-700/50 hover:bg-white/5 text-slate-300 font-bold text-sm transition-all flex items-center justify-center gap-2"
                        >
                            <ExternalLink className="w-4 h-4" /> Continue as Guest (View Public Projects)
                        </button>
                    </div>
                </div>

                <p className="text-center text-slate-600 text-[11px] mt-4">
                    Keys are stored locally in your browser. They are never sent to any third party.
                </p>
            </motion.div>
        </div>
    );
}
