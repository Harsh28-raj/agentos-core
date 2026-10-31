import { Card } from '../common/Card'
import type { LogEntry } from '../../types'
import { accent, muted, panel, panelTitle, tile } from './styles'

function describe(log: LogEntry): string {
  if (log.action_taken) {
    const args = log.modified_args ?? log.original_args ?? {}
    const what = String(args.summary ?? args.subject ?? args.action ?? args.tool ?? 'action')
    const verb = { CONFIRM: 'Approved', REJECT: 'Rejected', EDIT: 'Edited and approved' }[log.action_taken] ?? log.action_taken
    return `${verb}: ${what}`
  }
  return `${log.tool_name}: ${(log.tool_output?.output ?? '').slice(0, 160)}`
}

/** Episodic memory: human decisions and tool results of this conversation (audit log). */
export function MemoryViewer({ logs, error }: { logs: LogEntry[]; error: string }) {
  const entries = logs
    .filter((log) => log.action_taken || (log.status === 'completed' && log.tool_output?.output))
    .slice(-6)
    .reverse()

  return (
    <Card title={<span className={panelTitle}>EPISODIC MEMORY</span>} className={panel}>
      <div className="space-y-4">
        {error && <div className="text-xs font-mono text-red-500">{error}</div>}
        {!error && entries.length === 0 && <div className={`text-xs font-mono ${muted}`}>Nothing recorded for this conversation yet.</div>}
        {entries.map((log) => (
          <div key={log.id} className="text-sm">
            <div className={`font-mono text-[10px] mb-1 ${accent}`}>
              {log.created_at ? new Date(log.created_at + 'Z').toLocaleString() : ''}
            </div>
            <div className={`${tile} font-body leading-relaxed text-neutral-700 dark:text-neutral-300 break-words`}>{describe(log)}</div>
          </div>
        ))}
      </div>
    </Card>
  )
}
