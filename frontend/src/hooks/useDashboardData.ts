import { useCallback, useEffect, useState } from 'react'
import { chatService } from '../services/chatService'
import type { LogEntry, SystemStatus } from '../types'

/** Audit log of one thread, re-fetched whenever `refreshKey` changes. */
export function useThreadLogs(threadId: string, refreshKey: number) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    // Tool rows are written in the background right after a turn, so give them a moment
    const timer = setTimeout(() => {
      chatService
        .logs(threadId)
        .then((res) => !cancelled && (setLogs(res.logs), setError('')))
        .catch((err) => !cancelled && setError(err instanceof Error ? err.message : 'Could not load logs'))
    }, refreshKey ? 400 : 0)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [threadId, refreshKey])

  return { logs, error }
}

/** Live tool/integration status from GET /system/status, polled every minute. */
export function useSystemStatus(refreshKey = 0) {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    chatService
      .systemStatus()
      .then((res) => (setStatus(res), setError('')))
      .catch((err) => setError(err instanceof Error ? err.message : 'Backend unreachable'))
  }, [])

  useEffect(() => {
    load()
    const timer = setInterval(load, 60_000)
    return () => clearInterval(timer)
  }, [load, refreshKey])

  return { status, error, reload: load }
}
