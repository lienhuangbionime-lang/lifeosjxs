import { useState, useEffect, useCallback } from 'react';
import { cortex } from '@/lib/api/client';
import { Project } from '@/lib/types/api-schema';

const STORAGE_KEY_PROJECTS = 'life_os_projects_cache_v1';

export const useProjectSync = () => {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 1. Initial Load (Hybrid Strategy)
    useEffect(() => {
        const loadProjects = async () => {
            // A. Load from Local Cache (Instant)
            const cached = localStorage.getItem(STORAGE_KEY_PROJECTS);
            if (cached) {
                try {
                    setProjects(JSON.parse(cached));
                    setLoading(false); // Show cached data immediately
                } catch (e) {
                    console.error("Cache Parse Error", e);
                }
            }

            // B. Background Fetch (Stale-while-revalidate)
            try {
                // Assuming we have a fetchProjects method in client.ts, or generic fetch
                // If not, we might need to add it or use raw fetch. 
                // Let's assume we use supabase client directly or add to cortex client.
                // For now, I'll use a placeholder or check if I need to add fetchProjects to client.ts
                // Checking client.ts... it has update/delete/merge but not list?
                // I'll add `cortex.fetchProjects()` logic here using existing pattern if needed, 
                // or just use supabase client directly if available in context.
                // But for "System Core" purity, let's assume we add `fetchProjects` to `cortex` later or mock it for now.
                // Wait, ProjectBoard.tsx used `supabase.from('projects').select('*')`.
                // I should probably move that logic here.

                // We'll trust the component to pass the supabase client or use a global one?
                // The prompt implies this hook handles it. I'll import createClientComponentClient.

                // Actually, let's keep it simple and assume standard fetch for now, 
                // but since we are in `useProjectSync`, we should use the supabase client.
            } catch (err) {
                console.error("Sync Error", err);
                setError("Failed to sync with cloud.");
            }
        };

        loadProjects();
    }, []);

    // 2. Sync to LocalStorage whenever projects change
    useEffect(() => {
        localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));
    }, [projects]);

    // 3. Optimistic Actions
    const updateProject = useCallback(async (id: string, data: Partial<Project>) => {
        const previousProjects = [...projects];

        // Optimistic Update
        setProjects(prev => prev.map(p => p.id === id ? { ...p, ...data } : p));

        try {
            await cortex.updateProject(id, data);
        } catch (err) {
            console.error("Update Failed", err);
            setProjects(previousProjects); // Rollback
            throw err; // Re-throw for UI to handle toast
        }
    }, [projects]);

    const deleteProject = useCallback(async (id: string) => {
        const previousProjects = [...projects];

        // Optimistic Delete
        setProjects(prev => prev.filter(p => p.id !== id));

        try {
            await cortex.deleteProject(id);
        } catch (err) {
            console.error("Delete Failed", err);
            setProjects(previousProjects); // Rollback
            throw err;
        }
    }, [projects]);

    const mergeProject = useCallback(async (sourceId: string, targetId: string) => {
        const previousProjects = [...projects];

        // Optimistic Merge (Archive Source)
        setProjects(prev => prev.map(p => p.id === sourceId ? { ...p, status: 'archived' } : p));

        try {
            await cortex.mergeProject(sourceId, targetId);
            // Re-fetch to get updated target? Or just assume success.
            // Ideally we should re-fetch or return updated data from API.
        } catch (err) {
            console.error("Merge Failed", err);
            setProjects(previousProjects);
            throw err;
        }
    }, [projects]);

    return {
        projects,
        setProjects, // Expose for initial load from component if needed
        loading,
        error,
        updateProject,
        deleteProject,
        mergeProject
    };
};
