import { Card } from '../common/Card'
import { StatusBadge } from '../common/StatusBadge'
import type { Task } from '../../types'

export function TaskBoard() {
  const tasks: Task[] = [
    { id: '1', title: 'Summarize weekly reports', status: 'completed' },
    { id: '2', title: 'Monitor stock prices', status: 'in_progress' },
    { id: '3', title: 'Scrape documentation', status: 'pending' },
    { id: '4', title: 'Generate invoices', status: 'failed' },
  ]

  return (
    <Card title={<span className="font-mono text-white text-sm">ACTIVE TASKS</span>} className="h-full bg-[#0d0d0d] border-neutral-800 text-white transition-colors duration-200">
      <div className="space-y-3">
        {tasks.map((task) => (
          <div key={task.id} className="flex flex-col p-3 rounded-lg bg-neutral-900/40 border border-neutral-800/80 space-y-2 hover:border-neutral-600 transition-colors">
            <div className="flex justify-between items-start">
              <span className="font-body text-sm font-medium leading-tight text-neutral-200">{task.title}</span>
              <StatusBadge status={task.status} />
            </div>
            <div className="font-mono text-[10px] text-neutral-500 uppercase">
              ID: {task.id.padStart(4, '0')}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
