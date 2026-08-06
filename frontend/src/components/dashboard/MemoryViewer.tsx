import { Card } from '../common/Card'
import type { Memory } from '../../types'

export function MemoryViewer() {
  const memories: Memory[] = [
    { id: '1', content: 'User prefers dark mode.', timestamp: '2026-07-10T10:00:00Z' },
    { id: '2', content: 'Project deadlines are strictly on Fridays.', timestamp: '2026-07-12T14:30:00Z' },
    { id: '3', content: 'API keys are stored in Vault.', timestamp: '2026-07-13T09:15:00Z' },
  ]

  return (
    <Card title={<span className="font-mono text-white text-sm">EPISODIC MEMORY</span>} className="h-full bg-[#0d0d0d] border-neutral-800 text-white transition-colors duration-200">
      <div className="space-y-4">
        {memories.map((memory) => (
          <div key={memory.id} className="text-sm">
            <div className="font-mono text-[10px] text-emerald-500 mb-1">
              {new Date(memory.timestamp).toLocaleString()}
            </div>
            <div className="p-3 bg-neutral-900/40 border border-neutral-800/80 rounded-lg font-body leading-relaxed text-neutral-300">
              {memory.content}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
