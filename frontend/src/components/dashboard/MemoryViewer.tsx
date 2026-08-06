import { Card } from '../common/Card'
import type { Memory } from '../../types'

export function MemoryViewer() {
  const memories: Memory[] = [
    { id: '1', content: 'User prefers dark mode.', timestamp: '2026-07-10T10:00:00Z' },
    { id: '2', content: 'Project deadlines are strictly on Fridays.', timestamp: '2026-07-12T14:30:00Z' },
    { id: '3', content: 'API keys are stored in Vault.', timestamp: '2026-07-13T09:15:00Z' },
  ]

  return (
    <Card title="Episodic Memory" className="h-full">
      <div className="space-y-4">
        {memories.map((memory) => (
          <div key={memory.id} className="text-sm">
            <div className="font-mono text-[10px] text-slate mb-1">
              {new Date(memory.timestamp).toLocaleString()}
            </div>
            <div className="p-3 bg-surface border border-hairline rounded-base font-body leading-relaxed">
              {memory.content}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
