import { Card } from '../common/Card'
import { StatusBadge } from '../common/StatusBadge'
import type { LogEntry } from '../../types'
import { muted, panel, panelTitle, tile } from './styles'

interface ToolRun {
  id: string
  tool: string
  status: 'completed' | 'in_progress' | 'failed' | 'pending'
  at: string | null
}

/** Tool calls of the current conversation, built from the audit log. */
function toolRuns(logs: LogEntry[]): ToolRun[] {
  const runs = new Map<string, ToolRun>()
  for (const log of logs) {
    if (!log.tool_name || log.tool_name.startsWith('HITL_')) continue
    const output = log.tool_output?.output ?? ''
    const failed = /error|failed|cancelled/i.test(output.slice(0, 120))
    const status = log.status === 'completed' ? (failed ? 'failed' : 'completed') : log.status === 'awaiting_approval' ? 'pending' : 'in_progress'
    runs.set(log.run_id, { id: log.run_id, tool: log.tool_name, status, at: log.created_at })
  }
  // A tool paused for approval is re-run on resume: hide the paused attempt once a later run exists
  const ordered = [...runs.values()]
  const visible = ordered.filter(
    (run, i) => run.status !== 'pending' || !ordered.slice(i + 1).some((later) => later.tool === run.tool),
  )
  return visible.reverse().slice(0, 8)
}

export function TaskBoard({ logs, error }: { logs: LogEntry[]; error: string }) {
  const runs = toolRuns(logs)
  return (
    <Card title={<span className={panelTitle}>TOOL ACTIVITY</span>} className={panel}>
      <div className="space-y-3">
        {error && <div className="text-xs font-mono text-red-500">{error}</div>}
        {!error && runs.length === 0 && <div className={`text-xs font-mono ${muted}`}>No tool calls in this conversation yet.</div>}
        {runs.map((run) => (
          <div key={run.id} className={`flex flex-col space-y-2 ${tile}`}>
            <div className="flex justify-between items-start gap-2">
              <span className="font-mono text-sm text-neutral-800 dark:text-neutral-200 break-all">{run.tool}</span>
              <StatusBadge status={run.status} />
            </div>
            <div className={`font-mono text-[10px] uppercase ${muted}`}>
              {run.at ? new Date(run.at + 'Z').toLocaleTimeString() : ''}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
