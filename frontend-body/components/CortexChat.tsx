'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, MessageSquare, X, Bot, User, Loader2, Maximize2, Minimize2, Trash2, Settings, Terminal, Sparkles, Link2, Zap, Brain, Mic } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cortex, EvolutionStatus } from '@/lib/api/client';
import { CaptureView } from './CaptureView';
import { RadarView } from './RadarView';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export const CortexChat = ({ isInline = false, initialOpen = false }: { isInline?: boolean, initialOpen?: boolean }) => {
    const [isOpen, setIsOpen] = useState(initialOpen || isInline);
    const [isMaximized, setIsMaximized] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: 'Hello. I am **Cortex**, your digital assistant. How can I help you manage your projects and memories today?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [systemStatus, setSystemStatus] = useState<EvolutionStatus | null>(null);
    const [learningStatus, setLearningStatus] = useState<{ total: number; accuracy: number | null; count: number } | null>(null);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [availableModels, setAvailableModels] = useState<Array<{ id: string; name: string }>>([]);
    const [selectedModel, setSelectedModel] = useState('models/gemma-4-31b-it');
    const [isRefreshingModels, setIsRefreshingModels] = useState(false);
    const [apiKey, setApiKey] = useState('');
    const [activeTab, setActiveTab] = useState<'chat'>('chat');
    const [prompts, setPrompts] = useState<Record<string, string>>({});
    const [selectedPrompt, setSelectedPrompt] = useState('system_cortex');
    const [isSavingPrompt, setIsSavingPrompt] = useState(false);
    const [brainContext, setBrainContext] = useState<any | null>(null); // [New] Sovereign Context
    const [currentThought, setCurrentThought] = useState(''); // [New] Thinking Stream
    const [isRecording, setIsRecording] = useState(false);

    const scrollRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Load local settings
    useEffect(() => {
        const savedKey = localStorage.getItem('CORTEX_API_KEY');
        const savedModel = localStorage.getItem('CORTEX_MODEL');
        if (savedKey) setApiKey(savedKey);
        if (savedModel) {
            // [Hotfix] Reset if model is deprecated or corrupted
            if (savedModel.includes('pro-exp-02-05') || savedModel.includes('2.5') || savedModel.includes('-33') || savedModel.includes('1.5')) {
                setSelectedModel('models/gemini-2.0-flash-lite');
                localStorage.setItem('CORTEX_MODEL', 'models/gemini-2.0-flash-lite');
            } else if (savedModel.includes('gemini-3.0')) {
                // [Hotfix] Fix incorrect 3.0 version appearing in cache
                const fixed = savedModel.replace('gemini-3.0', 'gemini-3');
                setSelectedModel(fixed);
                localStorage.setItem('CORTEX_MODEL', fixed);
            } else {
                setSelectedModel(savedModel);
            }
        }

        const fetchStatus = async () => {
            try {
                const status = await cortex.checkEvolution();
                setSystemStatus(status);
            } catch (e) {
                console.error("Failed to fetch system status", e);
            }
        };
        fetchStatus();

        const fetchLearningStatus = async () => {
            try {
                const res = await cortex.brain.growth.getLessons(1);
                if (res) {
                    setLearningStatus({
                        total: res.total || 0,
                        accuracy: res.prediction_accuracy_pct,
                        count: res.judged_decisions || 0
                    });
                }
            } catch (e) {
                console.error("Failed to fetch learning status", e);
            }
        };
        fetchLearningStatus();

        // Load cached models
        const cachedModels = localStorage.getItem('CORTEX_AVAILABLE_MODELS');
        if (cachedModels) {
            try {
                setAvailableModels(JSON.parse(cachedModels));
            } catch (e) { console.error(e); }
        }
    }, []);

    const refreshModels = async () => {
        setIsRefreshingModels(true);
        try {
            const data = await cortex.getAvailableModels();
            if (data.models && data.models.length > 0) {
                setAvailableModels(data.models);
                localStorage.setItem('CORTEX_AVAILABLE_MODELS', JSON.stringify(data.models));
            }
        } catch (e) {
            console.error("Failed to refresh", e);
        } finally {
            setIsRefreshingModels(false);
        }
    };


    // Voice Recognition
    useEffect(() => {
        let recognition: any;
        if (isRecording) {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                // @ts-ignore
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = 'zh-TW';

                recognition.onresult = (event: any) => {
                    let finalTranscript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            finalTranscript += event.results[i][0].transcript;
                        }
                    }
                    if (finalTranscript) {
                        setInput(prev => prev + (prev ? ' ' : '') + finalTranscript);
                    }
                };

                recognition.onerror = (event: any) => {
                    setIsRecording(false);
                };

                recognition.start();
            } else {
                alert("Voice recognition not supported.");
                setIsRecording(false);
            }
        }
        return () => {
            if (recognition) recognition.stop();
        };
    }, [isRecording]);


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

    const [urlContext, setUrlContext] = useState<{ url: string; type: string; title: string; content: string; summary: string } | null>(null);
    const [isAnalyzingUrl, setIsAnalyzingUrl] = useState(false);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isOpen, urlContext]);

    const checkUrlInInput = async (text: string) => {
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const match = text.match(urlRegex);

        if (match && !urlContext && !isAnalyzingUrl) {
            const url = match[0];
            setIsAnalyzingUrl(true);
            try {
                const apiUrl = process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000';
                const res = await fetch(`${apiUrl}/api/v1/url/fetch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                if (res.ok) {
                    const data = await res.json();
                    setUrlContext(data);
                }
            } catch (e) {
                console.error("Failed to fetch URL context", e);
            } finally {
                setIsAnalyzingUrl(false);
            }
        }
    };

    const handleSend = async () => {
        if ((!input.trim() && !urlContext) || isLoading) return;

        const userMsg = input;
        const currentUrlContext = urlContext;

        setInput('');
        setUrlContext(null);
        setCurrentThought(''); // Reset thought

        const currentHistory = messages.map(m => ({
            role: m.role,
            content: m.content
        }));

        const displayMsg = currentUrlContext
            ? `[Discussing: ${currentUrlContext.title}](${currentUrlContext.url})\n\n${userMsg}`
            : userMsg;

        setMessages(prev => [...prev, { role: 'user', content: displayMsg }]);
        setIsLoading(true);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/v1/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg,
                    history: currentHistory,
                    model: selectedModel,
                    url_context: currentUrlContext
                })
            });

            if (!response.body) throw new Error('No stream');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';

            // Add initial empty message for the assistant
            setMessages(prev => [...prev, { role: 'assistant', content: currentUrlContext ? `*Integrating: ${currentUrlContext.title}...*` : '...' }]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                fullText += chunk;

                // [New] Thought Extraction Logic
                if (fullText.includes('<thought>')) {
                    const parts = fullText.split('<thought>');
                    const thoughtContent = parts[1]?.split('</thought>')[0] || parts[1] || '';
                    setCurrentThought(thoughtContent);
                }

                // Clean the text for the chat bubble (remove thought block)
                const chatDisplay = fullText.replace(/<thought>[\s\S]*?<\/thought>/g, '').trim();

                setMessages(prev => {
                    const newMsgs = [...prev];
                    const finalDisplay = chatDisplay || (fullText.includes('<thought>') && !fullText.includes('</thought>') ? 'Thinking...' : '...');
                    newMsgs[newMsgs.length - 1].content = finalDisplay;
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

    if (isInline) {
        return (
            <div className="flex flex-col w-full h-[calc(100vh-120px)] bg-white border border-slate-200 rounded-[32px] overflow-hidden shadow-sm">
                <div className="bg-slate-50 border-b border-slate-200 p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white">
                            <Bot size={20} />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-tight">Cortex Sovereign Engine</h3>
                            <div className="flex items-center gap-1.5">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest">Active • Neural Linked</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button onClick={() => setIsSettingsOpen(!isSettingsOpen)} className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-xl transition-colors">
                            <Settings size={18} />
                        </button>
                        <button onClick={clearChat} className="p-2 text-slate-400 hover:text-red-600 hover:bg-slate-100 rounded-xl transition-colors">
                            <Trash2 size={18} />
                        </button>
                    </div>
                </div>

                {/* Tab Navigation (Simple) */}
                <div className="flex bg-slate-50/50 border-b border-slate-100 px-6 py-2 gap-8 overflow-x-auto no-scrollbar">
                    <button
                        className="text-[11px] font-black uppercase tracking-[0.2em] pb-1 border-b-2 text-indigo-600 border-indigo-600"
                    >
                        Neural Dialogue
                    </button>
                </div>

                {isSettingsOpen && (
                    <div className="absolute inset-x-0 top-[110px] bottom-0 bg-white/95 backdrop-blur-md z-50 p-8 flex flex-col animate-in fade-in slide-in-from-top-2 duration-200">
                        <h4 className="text-xs font-black text-slate-400 uppercase tracking-[0.3em] mb-6">Sovereign Configurations</h4>
                        {/* reuse setting content or just link it */}
                        <div className="space-y-6 max-w-md">
                            <div>
                                <label className="block text-[10px] font-black text-slate-500 uppercase mb-2">Neural Model</label>
                                <select
                                    value={selectedModel}
                                    onChange={(e) => setSelectedModel(e.target.value)}
                                    className="w-full bg-slate-900 border border-slate-800 text-white rounded-2xl p-3 text-sm outline-none"
                                >
                                    {availableModels.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                                </select>
                            </div>
                        </div>
                        <button onClick={saveSettings} className="mt-8 bg-indigo-600 text-white p-4 rounded-2xl font-black uppercase tracking-widest text-xs">Authorize Changes</button>
                    </div>
                )}

                {/* Chat content - flex-1 */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-white scroll-smooth" ref={scrollRef}>
                    {messages.map((m, i) => (
                        <div key={i} className={`flex gap-4 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className={`shrink-0 w-10 h-10 rounded-2xl flex items-center justify-center shadow-lg ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-900 text-slate-300'}`}>
                                {m.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                            </div>
                            <div className={`max-w-[80%] rounded-[24px] p-5 text-sm leading-relaxed shadow-xl border
                                ${m.role === 'user'
                                    ? 'bg-indigo-600 text-white rounded-tr-none border-indigo-500'
                                    : 'bg-slate-50 text-slate-800 border-slate-100 rounded-tl-none'}`}
                            >
                                {m.role === 'assistant' ? (
                                    <div className="markdown-content">
                                        <ReactMarkdown
                                            components={{
                                                h1: ({ ...props }) => <h1 className="text-slate-900 font-bold text-lg mb-2" {...props} />,
                                                p: ({ ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                                code: ({ ...props }) => <code className="bg-slate-200 text-indigo-700 rounded px-1" {...props} />,
                                                pre: ({ ...props }) => <pre className="bg-slate-900 text-slate-100 p-4 rounded-2xl my-3 overflow-x-auto text-xs" {...props} />
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
                    {isLoading && (
                        <div className="text-xs text-indigo-500 font-black tracking-widest uppercase flex items-center gap-2 animate-pulse pl-14">
                            <Sparkles size={14} /> Neural processing...
                        </div>
                    )}
                </div>

                {/* Input area */}
                <div className="p-6 bg-slate-50/30 border-t border-slate-100">
                    <div className="bg-white border-2 border-slate-100 rounded-[28px] p-2 flex items-end gap-3 shadow-lg focus-within:border-indigo-500/30 transition-all">
                        <button onClick={() => fileInputRef.current?.click()} className="p-3 text-slate-400 hover:text-indigo-600 rounded-2xl transition-all"><Paperclip size={20} /></button>
                        <button onClick={() => setIsRecording(!isRecording)} className={`p-3 rounded-2xl transition-all ${isRecording ? 'bg-red-500 text-white animate-pulse shadow-lg' : 'text-slate-400 hover:text-indigo-600'}`}><Mic size={20} /></button>
                        <textarea
                            value={input}
                            onChange={e => { setInput(e.target.value); checkUrlInInput(e.target.value); }}
                            placeholder="Interrogate Cortex..."
                            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                            className="flex-1 bg-transparent border-0 px-3 py-3 text-sm text-slate-800 outline-none resize-none h-12 max-h-48"
                        />
                        <button onClick={handleSend} disabled={isLoading || (!input.trim() && !urlContext)} className="w-12 h-12 bg-indigo-600 text-white rounded-2xl flex items-center justify-center hover:bg-indigo-700 transition-all shadow-lg active:scale-95 disabled:opacity-30"><Send size={20} /></button>
                    </div>
                    {(urlContext || isAnalyzingUrl) && (
                        <div className="mt-4 p-3 bg-indigo-600/5 border border-indigo-500/10 rounded-2xl flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Link2 size={16} className="text-indigo-500" />
                                <span className="text-xs font-bold text-indigo-900 truncate">{urlContext?.title || 'Analyzing URL...'}</span>
                            </div>
                            <button onClick={() => setUrlContext(null)} className="text-indigo-400 hover:text-indigo-600"><X size={16} /></button>
                        </div>
                    )}
                </div>
            </div>
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
            <div className="flex bg-slate-50/50 border-b border-slate-100 px-3 py-1 gap-4 shrink-0 overflow-x-auto no-scrollbar">
                <button
                    onClick={() => setActiveTab('chat')}
                    className={`text-[10px] font-bold uppercase tracking-widest pb-1 border-b-2 transition-all shrink-0 ${activeTab === 'chat' ? 'text-indigo-600 border-indigo-600' : 'text-slate-400 border-transparent hover:text-slate-600'}`}
                >
                    Chat
                </button>
            </div>

            {/* Settings Overlay */}
            {isSettingsOpen && (
                <div className="absolute inset-x-0 top-[88px] bottom-0 bg-white/95 backdrop-blur-sm z-50 p-5 flex flex-col animate-in fade-in slide-in-from-top-2 duration-200">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Settings</h4>

                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between items-center mb-1.5">
                                <label className="block text-[10px] font-bold text-slate-500 uppercase">Model</label>
                                <button
                                    onClick={refreshModels}
                                    disabled={isRefreshingModels}
                                    className="text-[10px] text-indigo-500 hover:text-indigo-700 font-bold uppercase flex items-center gap-1 disabled:opacity-50"
                                >
                                    {isRefreshingModels ? <Loader2 size={10} className="animate-spin" /> : <Sparkles size={10} />}
                                    {isRefreshingModels ? 'Refreshing...' : 'Refresh List'}
                                </button>
                            </div>
                            <select
                                value={selectedModel}
                                onChange={(e) => setSelectedModel(e.target.value)}
                                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-indigo-100"
                            >
                                {availableModels.length > 0 ? (
                                    availableModels.map(model => (
                                        <option key={model.id} value={model.id}>
                                            {model.name}
                                        </option>
                                    ))
                                ) : (
                                    <>
                                        <option value="models/gemini-2.0-flash-lite">Gemini Flash Lite (Fast)</option>
                                        <option value="models/gemini-3.1-pro-preview">Gemini 3.1 Pro (Smart)</option>
                                        <option value="models/gemini-2.5-flash">Gemini 2.5 Flash (Reserve)</option>
                                    </>
                                )}
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
                                                    code: ({ ...props }) => (
                                                        <code className="bg-slate-200/50 text-indigo-700 rounded px-1 py-0.5 font-mono text-xs" {...props} />
                                                    ),
                                                    pre: ({ ...props }) => (
                                                        <pre className="bg-slate-800 text-slate-100 p-3 rounded-xl my-3 overflow-x-auto text-[11px] font-mono shadow-inner" {...props} />
                                                    ),
                                                    blockquote: ({ ...props }) => {
                                                        const isAction = String(props.children).includes('[Cortex Action]');
                                                        return (
                                                            <blockquote 
                                                                className={`border-l-4 pl-3 py-1 my-3 italic text-xs rounded-r-lg ${
                                                                    isAction 
                                                                    ? 'border-indigo-500 bg-indigo-50 text-indigo-900 font-bold not-italic font-mono' 
                                                                    : 'border-slate-300 bg-slate-50 text-slate-600'
                                                                }`} 
                                                                {...props} 
                                                            />
                                                        );
                                                    }
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
                            <button
                                onClick={() => setIsRecording(!isRecording)}
                                className={`p-2 rounded-xl transition-all ${isRecording ? 'bg-red-500 text-white animate-pulse' : 'text-slate-400 hover:text-indigo-600 hover:bg-white'}`}
                                title="Voice input"
                            >
                                <Mic size={18} />
                            </button>
                            <input type="file" className="hidden" ref={fileInputRef} onChange={handleFileUpload} accept=".pdf,.txt,.md,.jpg,.jpeg,.png,.webp,.svg" />

                            <textarea
                                value={input}
                                onChange={e => {
                                    setInput(e.target.value);
                                    checkUrlInInput(e.target.value);
                                }}
                                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                                placeholder={isAnalyzingUrl ? "Analyzing Link..." : "Ask anything or paste a URL..."}
                                className="flex-1 bg-transparent border-0 px-2 py-2 text-sm text-slate-700 outline-none resize-none h-10 max-h-32 font-sans"
                                rows={1}
                            />

                            <button
                                onClick={handleSend}
                                disabled={(!input.trim() && !urlContext) || isLoading}
                                className="h-10 w-10 flex items-center justify-center bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-30 disabled:hover:bg-indigo-600 transition-all shadow-md shadow-indigo-100"
                            >
                                {isLoading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                            </button>
                        </div>

                        {/* URL Preview Card */}
                        {(urlContext || isAnalyzingUrl) && (
                            <div className="mt-2 mx-1 p-2 bg-indigo-50 border border-indigo-100 rounded-lg flex items-center justify-between animate-in slide-in-from-bottom-2 fade-in duration-300">
                                <div className="flex items-center gap-2 overflow-hidden">
                                    <div className="w-6 h-6 bg-indigo-100 text-indigo-600 rounded flex items-center justify-center shrink-0">
                                        {isAnalyzingUrl ? <Loader2 className="animate-spin w-3 h-3" /> : <Link2 size={14} />}
                                    </div>
                                    <div className="flex flex-col min-w-0">
                                        <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider">
                                            {isAnalyzingUrl ? 'ANALYZING URL...' : 'CONTEXT LOADED'}
                                        </span>
                                        <span className="text-xs text-indigo-900 font-medium truncate w-full">
                                            {urlContext?.title || 'Fetching content...'}
                                        </span>
                                    </div>
                                </div>
                                {!isAnalyzingUrl && (
                                    <button
                                        onClick={() => setUrlContext(null)}
                                        className="p-1 text-indigo-400 hover:text-indigo-700 hover:bg-indigo-100 rounded transition-colors"
                                    >
                                        <X size={14} />
                                    </button>
                                )}
                            </div>
                        )}

                        {/* Stats */}
                        <div className="flex justify-between items-center px-2 mt-2">
                            <div className="flex gap-4">
                                <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest shrink-0" title="Current Model">
                                    {systemStatus?.current_model?.replace('models/', '') || 'GEMINI-PRO'}
                                </div>
                                {learningStatus && (
                                    <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest hidden sm:flex gap-2" title="AI Evolution Metrics">
                                        <span>🧠 MEM: {learningStatus.total}</span>
                                        <span>|</span>
                                        <span className={learningStatus.accuracy && learningStatus.accuracy > 70 ? 'text-emerald-500' : ''}>
                                            ACC: {learningStatus.accuracy !== null ? `${learningStatus.accuracy}%` : 'N/A'}
                                        </span>
                                    </div>
                                )}
                            </div>
                            <div className="text-[9px] text-indigo-400 font-bold uppercase tracking-widest shrink-0 text-right">
                                {systemStatus?.remaining_requests || '0'} REQ LEFT
                            </div>
                        </div>
                    </div>


            <style jsx global>{`
                .scrollbar-hide::-webkit-scrollbar { display: none; }
                .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
            `}</style>
        </div>
    );
};
