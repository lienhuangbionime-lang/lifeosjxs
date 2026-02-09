// ... imports
import { useSettings } from '@/lib/hooks/useSettings';

// ... inside CaptureView component
export const CaptureView = ({ onSave }: CaptureViewProps) => {
  const { habits } = useSettings(); // Use hook

  // ... existing state ...
  // [AI Agent] Enhanced Regex Logic & Task Extraction
  // ...

  let detectedHabits = { ...entry.habits };
  habits.filter(h => h.active).forEach(h => {  // Use habits from hook
    if (text.toLowerCase().includes(h.id) || text.includes(h.label.split(' ')[0])) {
      detectedHabits[h.id] = true;
    }
  });

  // ...

  <div className="grid grid-cols-2 gap-3">
    {habits.filter(h => h.active).map(habit => { // Use habits from hook & filter active
      const Icon = CoreEngine.getIconComponent(habit.icon);
      const isActive = entry.habits[habit.id];
      return (
        <button key={habit.id} onClick={() => setEntry({ ...entry, habits: { ...entry.habits, [habit.id]: !isActive } })}
          className={`p-4 rounded-2xl border transition-all flex items-center justify-between ${isActive ? 'bg-slate-800 border-slate-800 text-white shadow-lg' : 'bg-white border-slate-100 text-slate-400'}`}>
          <span className="text-xs font-bold">{habit.label}</span><Icon className={`w-5 h-5 ${isActive ? 'opacity-100' : 'opacity-20'}`} />
        </button>
      );
    })}
  </div>
// ...