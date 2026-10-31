import { useState } from 'react'
import { Check, Pencil, X } from 'lucide-react'
import type { ApprovalAction, InterruptData } from '../../types'

const HIDDEN_KEYS = new Set(['message', 'tool', 'action'])
const READ_ONLY_KEYS = new Set(['draft_id'])
const LABELS: Record<string, string> = {
  send_email: 'Send email',
  create_calendar_event: 'Create calendar event',
}

interface Props {
  data: InterruptData
  pendingCount?: number
  busy: boolean
  onDecide: (action: ApprovalAction, updatedArgs?: Record<string, unknown>) => void
}

function display(value: unknown): string {
  if (Array.isArray(value)) return value.join(', ')
  if (value === null || value === undefined) return ''
  return String(value)
}

/** Approve / Reject / Edit card for an action paused by a tool's interrupt(). */
export function ApprovalCard({ data, pendingCount = 1, busy, onDecide }: Props) {
  const fields = Object.entries(data).filter(([key, value]) => !HIDDEN_KEYS.has(key) && value !== null && value !== '')
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<Record<string, string>>(() =>
    Object.fromEntries(fields.map(([key, value]) => [key, display(value)])),
  )

  const submitEdit = () => {
    const updated: Record<string, unknown> = {}
    for (const [key, value] of fields) {
      if (READ_ONLY_KEYS.has(key) || draft[key] === display(value)) continue
      updated[key] = Array.isArray(value) ? draft[key].split(',').map((s) => s.trim()).filter(Boolean) : draft[key]
    }
    if (Object.keys(updated).length === 0) onDecide('CONFIRM')
    else onDecide('EDIT', updated)
  }

  const title = LABELS[data.tool ?? ''] ?? data.action ?? 'Action'

  return (
    <div className="rounded-lg border border-amber-500/40 bg-amber-50 dark:bg-amber-500/5 p-4 font-mono text-sm space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-amber-700 dark:text-amber-400 font-bold uppercase tracking-wider text-xs">
          ⏸ Approval required: {title}
        </span>
        {pendingCount > 1 && <span className="text-xs text-neutral-500">{pendingCount} actions</span>}
      </div>

      <dl className="space-y-2">
        {fields.map(([key, value]) => (
          <div key={key} className="grid grid-cols-[110px_1fr] gap-2 items-start">
            <dt className="text-neutral-500 dark:text-neutral-400 text-xs uppercase pt-1">{key.replace(/_/g, ' ')}</dt>
            <dd className="text-neutral-800 dark:text-neutral-200 break-words">
              {editing && !READ_ONLY_KEYS.has(key) ? (
                key === 'body' || key === 'description' ? (
                  <textarea
                    value={draft[key]}
                    onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
                    rows={4}
                    className="w-full rounded border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-2 py-1 text-sm"
                  />
                ) : (
                  <input
                    value={draft[key]}
                    onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
                    className="w-full rounded border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-2 py-1 text-sm"
                  />
                )
              ) : (
                <span className="whitespace-pre-wrap">{display(value)}</span>
              )}
            </dd>
          </div>
        ))}
      </dl>

      <div className="flex flex-wrap gap-2 pt-1">
        {editing ? (
          <>
            <button disabled={busy} onClick={submitEdit} className="inline-flex items-center gap-1 rounded bg-emerald-600 px-3 py-1.5 text-white hover:bg-emerald-500 disabled:opacity-50">
              <Check size={14} /> Save &amp; approve
            </button>
            <button disabled={busy} onClick={() => setEditing(false)} className="rounded border border-neutral-300 dark:border-neutral-700 px-3 py-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-50">
              Cancel edit
            </button>
          </>
        ) : (
          <>
            <button disabled={busy} onClick={() => onDecide('CONFIRM')} className="inline-flex items-center gap-1 rounded bg-emerald-600 px-3 py-1.5 text-white hover:bg-emerald-500 disabled:opacity-50">
              <Check size={14} /> Approve
            </button>
            <button disabled={busy} onClick={() => onDecide('REJECT')} className="inline-flex items-center gap-1 rounded bg-red-600 px-3 py-1.5 text-white hover:bg-red-500 disabled:opacity-50">
              <X size={14} /> Reject
            </button>
            {fields.length > 0 && (
              <button disabled={busy} onClick={() => setEditing(true)} className="inline-flex items-center gap-1 rounded border border-neutral-300 dark:border-neutral-700 px-3 py-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-50">
                <Pencil size={14} /> Edit
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}
