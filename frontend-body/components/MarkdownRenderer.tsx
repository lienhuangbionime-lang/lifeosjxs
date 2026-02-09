'use client';

import React, { memo } from 'react';

export const MarkdownRenderer = memo(({ content }: { content: string }) => {
    if (!content) return <div className="text-slate-300 italic text-sm text-center py-10">尚無內容</div>;
    return (
        <div className="space-y-3 text-slate-700 text-sm font-mono leading-relaxed">
            {content.split('\n').map((line, i) => {
                if (line.startsWith('# ')) return <h3 key={i} className="text-lg font-bold text-indigo-700 mt-4 border-b border-indigo-100 pb-1">{line.replace('# ', '')}</h3>;
                if (line.startsWith('## ')) return <h4 key={i} className="text-base font-bold text-slate-800 mt-3 flex items-center gap-2"><div className="w-1 h-4 bg-indigo-500 rounded-full" />{line.replace('## ', '')}</h4>;
                if (line.startsWith('> ')) return <div key={i} className="border-l-4 border-indigo-200 pl-3 py-2 my-2 bg-slate-50 text-slate-600 italic rounded-r-lg">{line.replace('> ', '')}</div>;
                return <p key={i} className="min-h-[1em]">{line}</p>;
            })}
        </div>
    );
});
