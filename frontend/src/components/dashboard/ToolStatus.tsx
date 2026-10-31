import { useEffect, useState } from 'react'
import { Loader2, XCircle } from 'lucide-react'
import { Card } from '../common/Card'
import { useSystemStatus } from '../../hooks/useDashboardData'
import { chatService } from '../../services/chatService'
import { muted, panel, panelTitle, tile } from './styles'

export function ToolStatus() {
  const { status, error, reload } = useSystemStatus()
  const [google, setGoogle] = useState<{ configured: boolean; connected: boolean } | null>(null)
  const [busy, setBusy] = useState(false)
  // Result of the Google OAuth redirect (?google=connected|error)
  const [notice, setNotice] = useState(() => {
    const result = new URLSearchParams(window.location.search).get('google')
    if (!result) return ''
    return result === 'connected' ? 'Google account connected.' : 'Google connection failed. Please try again.'
  })

  useEffect(() => {
    chatService.googleStatus().then(setGoogle).catch(() => setGoogle(null))
    const params = new URLSearchParams(window.location.search)
    if (params.has('google')) {
      params.delete('google')
      const query = params.toString()
      window.history.replaceState({}, '', `${window.location.pathname}${query ? `?${query}` : ''}`)
    }
  }, [])

  const connect = async () => {
    setBusy(true)
    try {
      window.location.href = (await chatService.googleAuthorize()).url
    } catch (err) {
      setNotice(err instanceof Error ? err.message : 'Could not start Google sign-in')
      setBusy(false)
    }
  }

  const disconnect = async () => {
    setBusy(true)
    try {
      setGoogle(await chatService.googleDisconnect().then((r) => ({ configured: google?.configured ?? true, connected: r.connected })))
      reload()
    } finally {
      setBusy(false)
    }
  }

  const googleButton = google?.configured && (
    <button
      onClick={google.connected ? disconnect : connect}
      disabled={busy}
      className="text-[10px] font-mono uppercase px-2 py-1 rounded border border-emerald-600/50 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 disabled:opacity-50"
    >
      {google.connected ? 'Disconnect Google' : 'Connect Google'}
    </button>
  )

  return (
    <Card title={<span className={panelTitle}>TOOL CONNECTIONS</span>} className={panel} headerAction={googleButton}>
      <div className="space-y-3">
        {notice && <div className="text-xs font-mono text-amber-600 dark:text-amber-400">{notice}</div>}
        {error && <div className="text-xs font-mono text-red-500">{error}</div>}
        {!status && !error && <Loader2 size={16} className="animate-spin text-emerald-500" />}
        {status?.tools.map((tool) => (
          <div key={tool.name} className={`flex justify-between items-center ${tile}`}>
            <div className="min-w-0">
              <div className="font-mono text-xs text-neutral-700 dark:text-neutral-300">{tool.name}</div>
              <div className={`font-mono text-[10px] truncate ${muted}`}>{tool.detail}</div>
            </div>
            <div className="flex items-center space-x-2 shrink-0">
              {tool.status === 'ONLINE' ? (
                <>
                  <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-500 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-900">ONLINE</span>
                  <span className="relative flex h-3 w-3 items-center justify-center">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500 shadow-[0_0_8px_#22c55e]" />
                  </span>
                </>
              ) : (
                <>
                  <span className="text-[10px] font-mono text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 px-2 py-0.5 rounded border border-red-200 dark:border-red-900">OFFLINE</span>
                  <XCircle size={14} className="text-red-500" />
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
