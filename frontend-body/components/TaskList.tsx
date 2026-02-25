
'use client';
import React, { useEffect, useState, useRef } from 'react';
import { CheckCircle, Circle, Loader2, Plus } from 'lucide-react';
import { cortex } from '@/lib/api/client';

interface Task {
    id: string;
    title: string;
    status: 'todo' | 'done' | 'archived';
    created_at: string;
}

interface TaskListProps {
    projectId?: string; // Optional: filter by project
    lastUpdate?: number; // Trigger refresh
}

export const TaskList = ({ projectId, lastUpdate }: TaskListProps) => {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [newTaskTitle, setNewTaskTitle] = useState('');
    const [isAdding, setIsAdding] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const fetchTasks = async () => {
        try {
            const data = await cortex.getTasks(projectId);
            setTasks(data);
        } catch (e) {
            console.error("Failed to fetch tasks", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
    }, [projectId, lastUpdate]);

    const handleComplete = async (taskId: string) => {
        // Optimistic Update
        setTasks(prev => prev.filter(t => t.id !== taskId));

        try {
            await cortex.completeTask(taskId);
        } catch (e) {
            console.error("Failed to complete task", e);
            // Revert on failure (simplified: just refetch)
            fetchTasks();
        }
    };

    const handleCreateTask = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        const title = newTaskTitle.trim();
        if (!title) return;

        setIsAdding(true);
        try {
            await cortex.createTask(title, projectId);
            setNewTaskTitle('');
            fetchTasks();
        } catch (error) {
            console.error("Failed to create task", error);
            alert("新增任務失敗，請稍後再試。");
        } finally {
            setIsAdding(false);
        }
    };

    if (loading) return <div className="p-4 flex justify-center"><Loader2 className="animate-spin text-indigo-500" size={16} /></div>;

    if (tasks.length === 0) return null; // Don't show if empty

    return (
        <div className="mt-4 border-t border-white/10 pt-3 px-4 pb-2">
            <h4 className="text-[10px] uppercase text-gray-500 font-bold tracking-wider mb-2">Active Tasks</h4>
            <div className="space-y-2">
                {tasks.map(task => (
                    <div key={task.id} className="group flex items-start gap-3 hover:bg-white/5 p-1.5 rounded-lg transition-colors cursor-pointer" onClick={() => handleComplete(task.id)}>
                        <div className="mt-0.5 text-gray-400 group-hover:text-indigo-400 transition-colors">
                            <Circle size={16} />
                        </div>
                        <span className="text-sm text-gray-300 group-hover:text-white leading-tight">
                            {task.title}
                        </span>
                    </div>
                ))}
            </div>

            <form onSubmit={handleCreateTask} className="mt-2 flex items-center gap-2 px-1">
                <input
                    ref={inputRef}
                    type="text"
                    value={newTaskTitle}
                    onChange={(e) => setNewTaskTitle(e.target.value)}
                    placeholder="新增任務..."
                    className="flex-1 bg-transparent border-none outline-none text-sm text-slate-300 placeholder-slate-600 font-medium"
                    disabled={isAdding}
                />
                <button
                    type="submit"
                    disabled={!newTaskTitle.trim() || isAdding}
                    className="p-1.5 text-slate-500 hover:text-indigo-400 disabled:opacity-50 transition-colors"
                >
                    {isAdding ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                </button>
            </form>
        </div>
    );
};
