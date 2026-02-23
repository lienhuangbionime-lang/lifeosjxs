import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Sparkles, Loader2, RefreshCw, Copy, Check } from 'lucide-react';

interface ReviewCardProps {
    month: string; // format "YYYY-MM"
}

export const ReviewCard = ({ month }: ReviewCardProps) => {
    const [review, setReview] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        fetchReview();
    }, [month]);

    const fetchReview = async () => {
        setLoading(true);
        setError(null);
        try {
            const [y, m] = month.split('-');
            const apiUrl = process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/v1/memories/review/${y}/${parseInt(m)}`);

            if (res.ok) {
                const data = await res.json();
                if (data && data.summary) {
                    setReview(data.summary);
                } else {
                    setReview(null);
                }
            } else {
                setReview(null);
            }
        } catch (e) {
            console.error("Failed to fetch review", e);
            setError("Failed to load review");
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = async () => {
        setGenerating(true);
        try {
            const [y, m] = month.split('-');
            const apiUrl = process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/v1/memories/review/${y}/${parseInt(m)}/generate`, {
                method: 'POST'
            });

            if (res.ok) {
                // Background task started
                // Poll for result or just show message
                setError(null);
                // Start polling
                const pollInterval = setInterval(async () => {
                    const checkRes = await fetch(`${apiUrl}/api/v1/memories/review/${y}/${parseInt(m)}`);
                    if (checkRes.ok) {
                        const data = await checkRes.json();
                        if (data && data.summary) {
                            setReview(data.summary);
                            setGenerating(false);
                            clearInterval(pollInterval);
                        }
                    }
                }, 5000); // Check every 5s

                // Timeout after 2 minutes
                setTimeout(() => {
                    clearInterval(pollInterval);
                    if (generating) {
                        setGenerating(false);
                        setError("Generation is taking longer than expected. Please check back later.");
                    }
                }, 120000);
            } else {
                setError("Failed to start generation");
                setGenerating(false);
            }
        } catch (e) {
            console.error("Failed to generate review", e);
            setError("Failed to trigger generation");
            setGenerating(false);
        }
    };

    const handleCopy = () => {
        if (review) {
            navigator.clipboard.writeText(review);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center text-slate-500">
                <Loader2 className="w-8 h-8 animate-spin" />
            </div>
        );
    }

    if (review) {
        return (
            <div className="h-full flex flex-col">
                <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{review}</ReactMarkdown>
                    </div>
                </div>
                <div className="mt-4 pt-4 border-t border-slate-700/30 flex justify-between items-center">
                    <button
                        onClick={handleCopy}
                        className="text-xs flex items-center gap-2 text-slate-500 hover:text-indigo-400 transition-colors"
                    >
                        {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                        {copied ? 'Copied' : 'Copy Text'}
                    </button>

                    <button
                        onClick={handleGenerate}
                        disabled={generating}
                        className="text-xs flex items-center gap-2 text-slate-500 hover:text-indigo-400 transition-colors"
                    >
                        <RefreshCw className={`w-3 h-3 ${generating ? 'animate-spin' : ''}`} />
                        Regenerate
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col items-center justify-center gap-6 p-8 text-center">
            <div className="p-4 rounded-full bg-indigo-500/10 border border-indigo-500/20">
                <Sparkles className="w-12 h-12 text-indigo-400" />
            </div>
            <div>
                <h3 className="text-lg font-bold text-white mb-2">No Review Found</h3>
                <p className="text-sm text-slate-400">
                    AI hasn't analyzed your memories for {month} yet.
                </p>
            </div>

            {generating ? (
                <div className="flex flex-col items-center gap-3 text-slate-400">
                    <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
                    <span className="text-sm">Synthesizing memories... (~30s)</span>
                </div>
            ) : (
                <button
                    onClick={handleGenerate}
                    className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors shadow-lg shadow-indigo-500/20 flex items-center gap-2"
                >
                    <Sparkles className="w-4 h-4" />
                    Generate Review
                </button>
            )}

            {error && (
                <p className="text-xs text-rose-400 mt-2">{error}</p>
            )}
        </div>
    );
};
