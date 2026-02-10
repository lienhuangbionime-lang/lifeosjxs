'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, MessageSquare, X, Bot, User, FileText, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cortex, EvolutionStatus } from '@/lib/api/client';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export const CortexChat = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: 'Hello 蒼禾. I am Cortex. How can I assist you today?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [systemStatus, setSystemStatus] = useState<EvolutionStatus | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Fetch system status on mount
    useEffect(() => {
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

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isOpen]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/v1/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg })
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
            setMessages(prev => [...prev, { role: 'assistant', content: 'Connection lost with Cortex.' }]);
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
            const res = await fetch('http://localhost:8000/api/v1/chat/ingest', {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                setMessages(prev => [...prev, { role: 'assistant', content: `Creating synaptic connections for **${file.name}**... Done.` }]);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    return (
        <>
            {/* Trigger Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="fixed bottom-6 right-6 p-4 bg-slate-900 text-white rounded-full shadow-2xl hover:scale-110 transition-transform z-50 border border-slate-700"
            >
                {isOpen ? <X /> : <MessageSquare />}
            </button>

            {/* Chat Interface */}
            {isOpen && (
                <div className="fixed bottom-24 right-6 w-[400px] h-[600px] bg-white rounded-3xl shadow-2xl flex flex-col border border-slate-200 overflow-hidden z-50 animate-fade-in-up">
                    {/* Header */}
                    <div className="bg-slate-900 p-4 flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-slate-900 font-bold">
                            C
                        </div>
                        <div className="flex-1">
                            <h3 className="text-white font-bold text-sm">Cortex v3.1</h3>
                            <p className="text-slate-400 text-[10px] flex items-center gap-1">
                                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                                Online
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="text-[9px] text-slate-500 font-mono">
                                {systemStatus?.model_versions?.[1] || 'gemini-3.0-pro-preview'}
                            </div>
                            <div className="text-[8px] text-emerald-400 font-mono">
                                {systemStatus?.remaining_requests || 'N/A'}
                            </div>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 relative" ref={scrollRef}>
                        {messages.map((m, i) => (
                            <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${m.role === 'user' ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-200 text-slate-600'}`}>
                                    {m.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                                </div>
                                <div className={`max-w-[80%] rounded-2xl p-3 text-sm leading-relaxed shadow-sm ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white text-slate-700 border border-slate-100'}`}>
                                    {m.role === 'assistant' ? (
                                        <ReactMarkdown
                                            components={{
                                                code: ({ node, ...props }) => <code className="bg-slate-100 text-red-500 rounded px-1" {...props} />
                                            }}
                                        >
                                            {m.content}
                                        </ReactMarkdown>
                                    ) : (
                                        m.content
                                    )}
                                </div>
                            </div>
                        ))}
                        {isUploading && (
                            <div className="text-xs text-slate-400 flex items-center gap-2 pl-12">
                                <Loader2 className="animate-spin w-3 h-3" /> Processing knowledge...
                            </div>
                        )}
                        {isLoading && messages[messages.length - 1].role === 'user' && (
                            <div className="text-xs text-slate-400 flex items-center gap-2 pl-12">
                                <Loader2 className="animate-spin w-3 h-3" /> Thinking...
                            </div>
                        )}
                    </div>

                    {/* Input */}
                    <div className="p-3 bg-white border-t border-slate-100 flex items-end gap-2">
                        <button onClick={() => fileInputRef.current?.click()} className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-slate-50 rounded-xl transition-colors">
                            <Paperclip size={20} />
                        </button>
                        <input type="file" className="hidden" ref={fileInputRef} onChange={handleFileUpload} accept=".pdf,.txt,.md,.jpg,.jpeg,.png,.webp,.svg" />

                        <textarea
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                            placeholder="Ask Cortex..."
                            className="flex-1 bg-slate-50 border-0 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-100 outline-none resize-none h-10 max-h-24"
                        />

                        <button onClick={handleSend} disabled={!input.trim() || isLoading} className="p-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-lg shadow-indigo-200">
                            <Send size={18} />
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};
