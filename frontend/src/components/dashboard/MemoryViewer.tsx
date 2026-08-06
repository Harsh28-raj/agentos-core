import { Card } from '../common/Card'
import type { Memory } from '../../types'
import { Clock } from 'lucide-react'

export function MemoryViewer() {
  const memories: Memory[] = [
    { id: '1', content: 'User prefers dark mode.', timestamp: '2026-07-10T10:00:00Z' },
    { id: '2', content: 'Project deadlines are strictly on Fridays.', timestamp: '2026-07-12T14:30:00Z' },
    { id: '3', content: 'API keys are stored in Vault.', timestamp: '2026-07-13T09:15:00Z' },
  ]

  return (
    <Card title="EPISODIC MEMORY" className="h-full bg-[#0a0a0a] border-neutral-800 text-white transition-colors duration-200">
      <div className="space-y-3">
        {memories.map((memory) => (
          <div key={memory.id} className="bg-slate-50 dark:bg-neutral-900/40 border border-slate-200 dark:border-neutral-800/80 rounded-lg p-2.5 space-y-1 hover:border-slate-300 dark:hover:border-neutral-700/80 hover:bg-slate-100 hover:dark:bg-neutral-900/60 transition-colors duration-200">
            <div className="flex items-center gap-1.5 font-mono text-[10px] text-emerald-600 dark:text-emerald-400/80">
              <Clock size={12} />
              {new Date(memory.timestamp).toLocaleString()}
            </div>
            <div className="text-xs text-slate-600 dark:text-neutral-400 font-sans leading-relaxed">
              {memory.content}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
