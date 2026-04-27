'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, MessageSquare, X, Bot, User, Loader2, Maximize2, Minimize2, Trash2, Settings, Terminal, Sparkles, Link2, Zap, Brain, Mic, MicOff, Tv } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cortex, EvolutionStatus } from '@/lib/api/client';
import { CaptureView } from './CaptureView';
import { RadarView } from './RadarView';

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
    const [learningStatus, setLearningStatus] = useState<{ total: number; accuracy: number | null; count: number } | null>(null);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [availableModels, setAvailableModels] = useState<Array<{ id: string; name: string }>>([]);
    const [selectedModel, setSelectedModel] = useState('models/gemini-flash-lite-latest');
    const [isRefreshingModels, setIsRefreshingModels] = useState(false);
    const [apiKey, setApiKey] = useState('');
    const [activeTab, setActiveTab] = useState<'chat'>('chat');
    const [prompts, setPrompts] = useState<Record<string, string>>({});
    const [selectedPrompt, setSelectedPrompt] = useState('system_cortex');
    const [isSavingPrompt, setIsSavingPrompt] = useState(false);
    const [brainContext, setBrainContext] = useState<any | null>(null); // [New] Sovereign Context
    const [currentThought, setCurrentThought] = useState(''); // [New] Thinking Stream
    const [isConversationMode, setIsConversationMode] = useState(false); // [New] Immersive Mode
    const [isListening, setIsListening] = useState(false); // [New] Voice Input
    const recognitionRef = useRef<any>(null);

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
                setSelectedModel('models/gemma-4-31b-it');
                localStorage.setItem('CORTEX_MODEL', 'models/gemma-4-31b-it');
            } else if (savedModel.includes('gemini-3.0')) {
                // [Hotfix] Preferred Gemma-4 over experimental Gemini versions
                setSelectedModel('models/gemma-4-26b-a4b-it');
                localStorage.setItem('CORTEX_MODEL', 'models/gemma-4-26b-a4b-it');
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

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
        } else {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Browser does not support Speech Recognition.");
                return;
            }
            
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'zh-TW';
            
            recognition.onstart = () => setIsListening(true);
            recognition.onend = () => setIsListening(false);
            recognition.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript;
                setInput(prev => prev ? prev + ' ' + transcript : transcript);
            };
            recognition.onerror = (err: any) => {
                console.error("Speech Error:", err);
                setIsListening(false);
            };
            
            recognition.start();
            recognitionRef.current = recognition;
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
                    <button
                        onClick={() => setIsConversationMode(!isConversationMode)}
                        className={`p-1.5 rounded-lg transition-all ${isConversationMode ? 'bg-indigo-100 text-indigo-600' : 'text-slate-400 hover:text-indigo-600 hover:bg-slate-100'}`}
                        title={isConversationMode ? "Exit Conversation Mode" : "Enter Conversation Mode"}
                    >
                        <Tv size={16} />
                    </button>
                    {!isConversationMode && (
                        <>
                            <button onClick={() => setIsSettingsOpen(!isSettingsOpen)} className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors">
                                <Settings size={16} />
                            </button>
                            <button onClick={() => setIsMaximized(!isMaximized)} className="hidden sm:block p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors">
                                {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                            </button>
                            <button onClick={clearChat} className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-slate-100 rounded-lg transition-colors">
                                <Trash2 size={16} />
                            </button>
                        </>
                    )}
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
                                onClick={toggleListening}
                                className={`p-2 transition-all rounded-xl ${isListening ? 'bg-red-50 text-red-500 animate-pulse' : 'text-slate-400 hover:text-indigo-600 hover:bg-white'}`}
                                title={isListening ? "Stop Listening" : "Voice Input"}
                            >
                                {isListening ? <MicOff size={18} /> : <Mic size={18} />}
                            </button>

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
