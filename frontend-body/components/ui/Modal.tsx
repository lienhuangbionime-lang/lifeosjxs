'use client';
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
    title?: string;
    className?: string; // Additional classes for the container
}

export const Modal = ({ isOpen, onClose, children, title, className = '' }: ModalProps) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[150] flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-slate-900/60 backdrop-blur-md transition-all"
                    />

                    {/* Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        transition={{ type: "spring", duration: 0.3 }}
                        className={`bg-white/95 relative z-10 w-full rounded-3xl shadow-2xl overflow-hidden border border-white/20 ${className}`}
                    >
                        {title && (
                            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 cursor-grab active:cursor-grabbing">
                                <h3 className="font-bold text-slate-800 pointer-events-none">{title}</h3>
                                <button onClick={onClose} className="p-1 hover:bg-slate-200 rounded-full transition-colors text-slate-500" onPointerDown={(e) => e.stopPropagation()}>
                                    <X size={16} />
                                </button>
                            </div>
                        )}
                        <div className="p-0 cursor-auto flex-1 flex flex-col min-h-0" onPointerDown={(e) => e.stopPropagation()}>
                            {children}
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
};
