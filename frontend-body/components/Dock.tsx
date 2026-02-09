'use client';
import React from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Home, Layers, Brain, Settings, Plus } from 'lucide-react';

interface DockProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
    onMenuToggle?: () => void;
}

export const Dock = ({ activeTab, onTabChange }: DockProps) => {
    const mouseX = useMotionValue(Infinity);

    const items = [
        { id: 'dashboard', icon: Home, label: 'Home' },
        { id: 'project', icon: Layers, label: 'Projects' },
        { id: 'capture', icon: Plus, label: 'Capture' }, // Middle action? Or tab?
        { id: 'graph', icon: Brain, label: 'Brain' },
        { id: 'settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <div
            className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40 flex items-end gap-3 px-4 py-3 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl"
            onMouseMove={(e) => mouseX.set(e.pageX)}
            onMouseLeave={() => mouseX.set(Infinity)}
        >
            {items.map((item) => (
                <DockIcon
                    key={item.id}
                    mouseX={mouseX}
                    item={item}
                    isActive={activeTab === item.id}
                    onClick={() => onTabChange(item.id)}
                />
            ))}
        </div>
    );
};

function DockIcon({ mouseX, item, isActive, onClick }: { mouseX: any, item: any, isActive: boolean, onClick: () => void }) {
    const ref = React.useRef<HTMLDivElement>(null);

    const distance = useTransform(mouseX, (val: number) => {
        const bounds = ref.current?.getBoundingClientRect() ?? { x: 0, width: 0 };
        return val - bounds.x - bounds.width / 2;
    });

    const widthSync = useTransform(distance, [-150, 0, 150], [40, 60, 40]);
    const width = useSpring(widthSync, { mass: 0.1, stiffness: 150, damping: 12 });

    return (
        <motion.div
            ref={ref}
            style={{ width, height: width }}
            onClick={onClick}
            className={`cursor-pointer rounded-full flex items-center justify-center relative group transition-colors ${isActive ? 'bg-indigo-500 text-white' : 'bg-white/10 text-slate-300 hover:bg-white/20'}`}
        >
            <item.icon size={20} />
            <span className="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/80 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                {item.label}
            </span>
            {isActive && (
                <span className="absolute -bottom-2 w-1 h-1 bg-indigo-400 rounded-full" />
            )}
        </motion.div>
    );
}
