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
    <Card title="ACTIVE TASKS" className="h-full bg-white dark:bg-neutral-900/60 border-slate-200 dark:border-neutral-800/80 text-slate-800 dark:text-neutral-200 transition-colors duration-200">
      <div className="overflow-y-auto max-h-[280px] pr-1 custom-scrollbar space-y-2.5">
        {tasks.map((task) => (
          <div key={task.id} className="flex flex-col p-2.5 rounded-lg bg-slate-50 dark:bg-neutral-900/40 border border-slate-200 dark:border-neutral-800/80 space-y-2 hover:border-slate-300 dark:hover:border-neutral-700 hover:bg-slate-100 hover:dark:bg-neutral-900/60 transition-colors duration-200">
            <div className="flex justify-between items-start">
              <span className="font-body text-sm font-medium leading-tight text-slate-800 dark:text-neutral-200">{task.title}</span>
              <StatusBadge status={task.status} />
            </div>
            <div className="font-mono text-[10px] text-slate-600 dark:text-neutral-400">
              ID: {task.id.padStart(4, '0')}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
