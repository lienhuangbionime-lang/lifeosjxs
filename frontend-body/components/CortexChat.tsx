'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, MessageSquare, X, Bot, User, Loader2, Maximize2, Minimize2, Trash2, Settings, Terminal, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cortex, EvolutionStatus } from '@/lib/api/client';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export const CortexChat = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isMaximized, setIsMaximized] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: 'Hello. I am **Cortex**, your digital assistant. How can I help you manage your projects and memories today?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [systemStatus, setSystemStatus] = useState<EvolutionStatus | null>(null);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [selectedModel, setSelectedModel] = useState('gemini-3.0-pro-preview');
    const [apiKey, setApiKey] = useState('');
    const [activeTab, setActiveTab] = useState<'chat' | 'logic'>('chat');
    const [prompts, setPrompts] = useState<Record<string, string>>({});
    const [selectedPrompt, setSelectedPrompt] = useState('system_cortex');
    const [isSavingPrompt, setIsSavingPrompt] = useState(false);

    const scrollRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Load local settings
    useEffect(() => {
        const savedKey = localStorage.getItem('CORTEX_API_KEY');
        const savedModel = localStorage.getItem('CORTEX_MODEL');
        if (savedKey) setApiKey(savedKey);
        if (savedModel) setSelectedModel(savedModel);

        const fetchStatus = async () => {
            try {
                const status = await cortex.checkEvolution();
                setSystemStatus(status);
            } catch (e) {
                console.error("Failed to fetch system status", e);
            }
        };
        fetchStatus();
    }, []);

    // Fetch prompt content when activeTab or selectedPrompt changes
    useEffect(() => {
        if (activeTab === 'logic') {
            const fetchPrompt = async () => {
                try {
                    const data = await cortex.getPrompt(selectedPrompt);
                    setPrompts(prev => ({ ...prev, [selectedPrompt]: data.content }));
                } catch (e) {
                    console.error("Failed to fetch prompt", e);
                }
            };
            fetchPrompt();
        }
    }, [activeTab, selectedPrompt]);

    const handleSavePrompt = async () => {
        if (!prompts[selectedPrompt]) return;
        setIsSavingPrompt(true);
        try {
            await cortex.updatePrompt(selectedPrompt, prompts[selectedPrompt]);
            alert('Prompt updated successfully!');
        } catch (e) {
            console.error(e);
            alert('Failed to update prompt.');
        } finally {
            setIsSavingPrompt(false);
        }
    };

    useEffect(() => {
        if (scrollRef.current && activeTab === 'chat') {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isOpen, activeTab]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg = input;
        setInput('');

        const currentHistory = messages.map(m => ({
            role: m.role,
            content: m.content
        }));

        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsLoading(true);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/v1/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg,
                    history: currentHistory
                })
            });

            if (!response.body) throw new Error('No stream');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiMsg = '';

            setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                aiMsg += chunk;
                setMessages(prev => {
                    const newMsgs = [...prev];
                    newMsgs[newMsgs.length - 1].content = aiMsg;
                    return newMsgs;
                });
            }
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'assistant', content: '**Error**: Connection lost. Please check if the backend is running.' }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/v1/chat/ingest`, {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                setMessages(prev => [...prev, { role: 'assistant', content: `Successfully integrated **${file.name}** into my knowledge base.` }]);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const saveSettings = () => {
        localStorage.setItem('CORTEX_API_KEY', apiKey);
        localStorage.setItem('CORTEX_MODEL', selectedModel);
        setIsSettingsOpen(false);
    };

    const clearChat = () => {
        if (confirm('Clear conversation history?')) {
            setMessages([{ role: 'assistant', content: 'Conversation cleared.' }]);
        }
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 p-4 bg-indigo-600 text-white rounded-full shadow-lg hover:scale-105 transition-transform z-50 flex items-center justify-center"
            >
                <MessageSquare size={24} />
            </button>
        );
    }

    return (
        <div
            className={`fixed transition-all duration-300 z-[100] shadow-2xl flex flex-col bg-white border border-slate-200 overflow-hidden
            ${isMaximized
                    ? 'inset-0 w-full h-full'
                    : 'bottom-4 right-4 w-[calc(100%-2rem)] sm:w-[360px] h-[550px] max-h-[calc(100vh-2rem)] rounded-2xl'}`}
        >
            {/* Header */}
            <div className="bg-slate-50 border-b border-slate-200 p-3 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                        <Bot size={18} />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-slate-800">Cortex AI</h3>
                        <div className="flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            <span className="text-[10px] text-slate-500 font-medium uppercase tracking-tight">Active</span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-1">
                    <button onClick={() => setIsSettingsOpen(!isSettingsOpen)} className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors">
                        <Settings size={16} />
                    </button>
                    <button onClick={() => setIsMaximized(!isMaximized)} className="hidden sm:block p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors">
                        {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                    </button>
                    <button onClick={clearChat} className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-slate-100 rounded-lg transition-colors">
                        <Trash2 size={16} />
                    </button>
                    <button onClick={() => setIsOpen(false)} className="p-1.5 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors ml-1">
                        <X size={18} />
                    </button>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex bg-slate-50/50 border-b border-slate-100 px-3 py-1 gap-4 shrink-0">
                <button
                    onClick={() => setActiveTab('chat')}
                    className={`text-[10px] font-bold uppercase tracking-widest pb-1 border-b-2 transition-all ${activeTab === 'chat' ? 'text-indigo-600 border-indigo-600' : 'text-slate-400 border-transparent hover:text-slate-600'}`}
                >
                    Chat
                </button>
                <button
                    onClick={() => setActiveTab('logic')}
                    className={`text-[10px] font-bold uppercase tracking-widest pb-1 border-b-2 transition-all ${activeTab === 'logic' ? 'text-indigo-600 border-indigo-600' : 'text-slate-400 border-transparent hover:text-slate-600'}`}
                >
                    🧠 Logic
                </button>
            </div>

            {/* Settings Overlay */}
            {isSettingsOpen && (
                <div className="absolute inset-x-0 top-[88px] bottom-0 bg-white/95 backdrop-blur-sm z-50 p-5 flex flex-col animate-in fade-in slide-in-from-top-2 duration-200">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Settings</h4>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Model</label>
                            <select
                                value={selectedModel}
                                onChange={(e) => setSelectedModel(e.target.value)}
                                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-indigo-100"
                            >
                                <option value="gemini-pro-latest">Gemini Pro Latest</option>
                                <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                                <option value="gemini-3.0-pro-preview">Gemini 3.0 pro preview
                                </option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">API Key Override</label>
                            <input
                                type="password"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="Enter Key..."
                                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-indigo-100"
                            />
                        </div>
                    </div>

                    <div className="mt-auto flex gap-2">
                        <button
                            onClick={saveSettings}
                            className="flex-1 bg-indigo-600 text-white p-3 rounded-xl text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-100"
                        >
                            Save Changes
                        </button>
                    </div>
                </div>
            )}

            {/* Logic Tab Body */}
            {activeTab === 'logic' && (
                <div className="flex-1 flex flex-col p-4 bg-slate-50 overflow-hidden">
                    <div className="flex items-center justify-between mb-4">
                        <select
                            value={selectedPrompt}
                            onChange={(e) => setSelectedPrompt(e.target.value)}
                            className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-[11px] font-bold text-slate-600 outline-none"
                        >
                            <option value="system_cortex">Core Philosophy</option>
                            <option value="system_daily">Daily Analysis Logic</option>
                        </select>
                        <button
                            onClick={handleSavePrompt}
                            disabled={isSavingPrompt}
                            className="text-[10px] bg-indigo-600 text-white px-3 py-1.5 rounded-lg font-bold hover:bg-indigo-700 disabled:opacity-50"
                        >
                            {isSavingPrompt ? 'Saving...' : 'Update Brain'}
                        </button>
                    </div>
                    <textarea
                        value={prompts[selectedPrompt] || 'Loading...'}
                        onChange={(e) => setPrompts(prev => ({ ...prev, [selectedPrompt]: e.target.value }))}
                        className="flex-1 w-full bg-white border border-slate-200 rounded-xl p-3 text-xs font-mono text-slate-700 outline-none resize-none focus:ring-2 focus:ring-indigo-100"
                        placeholder="Customize Cortex's thinking..."
                    />
                    <div className="mt-3 p-3 bg-indigo-50 rounded-xl border border-indigo-100">
                        <h5 className="text-[10px] font-black text-indigo-600 uppercase mb-1 tracking-wider">Warning</h5>
                        <p className="text-[10px] text-indigo-500 leading-normal font-medium">
                            Modifying the brain files will change how Cortex perceives and analyzes your reality.
                        </p>
                    </div>
                </div>
            )}

            {/* Chat Body */}
            {activeTab === 'chat' && (
                <>
                    <div
                        className="flex-1 overflow-y-auto p-4 space-y-5 bg-white scroll-smooth"
                        ref={scrollRef}
                    >
                        {messages.map((m, i) => (
                            <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${m.role === 'user' ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-600'}`}>
                                    {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                                </div>

                                <div className={`max-w-[85%] rounded-2xl p-3 text-sm leading-relaxed shadow-sm
                                    ${m.role === 'user'
                                        ? 'bg-indigo-600 text-white rounded-tr-none'
                                        : 'bg-slate-50 text-slate-700 border border-slate-100 rounded-tl-none'}`}
                                >
                                    {m.role === 'assistant' ? (
                                        <div className="markdown-content">
                                            <ReactMarkdown
                                                components={{
                                                    h1: ({ ...props }) => <h1 className="text-slate-900 font-bold text-lg mb-2 border-b border-slate-200 pb-1" {...props} />,
                                                    h2: ({ ...props }) => <h2 className="text-slate-800 font-bold text-md mb-2" {...props} />,
                                                    p: ({ ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                                    ul: ({ ...props }) => <ul className="list-disc list-inside mb-2 space-y-1 text-slate-600 font-sans" {...props} />,
                                                    li: ({ ...props }) => <li className="text-slate-700" {...props} />,
                                                    strong: ({ ...props }) => <strong className="text-slate-900 font-bold" {...props} />,
                                                    code: ({ node, ...props }) => (
                                                        <code className="bg-slate-200/50 text-indigo-700 rounded px-1 py-0.5 font-mono text-xs" {...props} />
                                                    ),
                                                    pre: ({ node, ...props }) => (
                                                        <pre className="bg-slate-800 text-slate-100 p-3 rounded-xl my-3 overflow-x-auto text-[11px] font-mono shadow-inner" {...props} />
                                                    )
                                                }}
                                            >
                                                {m.content}
                                            </ReactMarkdown>

                                        </div>
                                    ) : (
                                        <div className="whitespace-pre-wrap">{m.content}</div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {isUploading && (
                            <div className="text-[11px] text-slate-400 flex items-center gap-2 pl-11">
                                <Loader2 className="animate-spin w-3 h-3" /> Processing content...
                            </div>
                        )}
                        {isLoading && messages[messages.length - 1].role === 'user' && (
                            <div className="text-[11px] text-indigo-500 flex items-center gap-2 pl-11 font-medium">
                                <Sparkles className="animate-pulse w-3 h-3" /> Cortex is thinking...
                            </div>
                        )}
                    </div>

                    {/* Input Area */}
                    <div className="p-3 bg-white border-t border-slate-100 shrink-0">
                        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-1.5 flex items-end gap-1.5 focus-within:ring-2 focus-within:ring-indigo-100 focus-within:border-indigo-200 transition-all">
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-white rounded-xl transition-all"
                                title="Upload"
                            >
                                <Paperclip size={18} />
                            </button>
                            <input type="file" className="hidden" ref={fileInputRef} onChange={handleFileUpload} accept=".pdf,.txt,.md,.jpg,.jpeg,.png,.webp,.svg" />

                            <textarea
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                                placeholder="Ask anything..."
                                className="flex-1 bg-transparent border-0 px-2 py-2 text-sm text-slate-700 outline-none resize-none h-10 max-h-32 font-sans"
                                rows={1}
                            />

                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || isLoading}
                                className="h-10 w-10 flex items-center justify-center bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-30 disabled:hover:bg-indigo-600 transition-all shadow-md shadow-indigo-100"
                            >
                                {isLoading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                            </button>
                        </div>

                        {/* Stats */}
                        <div className="flex justify-between items-center px-2 mt-2">
                            <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">
                                {systemStatus?.model_versions?.[1]?.replace('models/', '') || 'GEMINI-PRO'}
                            </div>
                            <div className="text-[9px] text-indigo-400 font-bold uppercase tracking-widest">
                                {systemStatus?.remaining_requests || '0'} REQUESTS LEFT
                            </div>
                        </div>
                    </div>
                </>
            )}

            <style jsx global>{`
                .scrollbar-hide::-webkit-scrollbar { display: none; }
                .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
            `}</style>
        </div>
    );
};
