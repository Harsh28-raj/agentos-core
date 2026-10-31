import { useEffect, useState } from 'react'
import { useSystemStatus } from '../../hooks/useDashboardData'

export function SystemStatusBar() {
  const [time, setTime] = useState(new Date())
  const { status, error } = useSystemStatus()

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const online = !error && status?.llm.status === 'ONLINE'
  return (
    <div className="flex items-center space-x-4 font-mono text-xs uppercase text-slate select-none">
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full animate-pulse ${online ? 'bg-signal' : 'bg-red-500'}`} />
        <span className={`font-display font-bold ${online ? 'text-signal' : 'text-red-500'}`}>
          {status ? (online ? 'SYSTEM ONLINE' : 'AGENT OFFLINE') : error ? 'BACKEND UNREACHABLE' : 'CONNECTING'}
        </span>
      </div>
      {status && (
        <>
          <span className="hidden sm:inline">|</span>
          <span className="hidden sm:inline">
            {status.active_tools}/{status.tools.length} TOOLS ACTIVE
          </span>
        </>
      )}
      <span className="hidden sm:inline">|</span>
      <span className="hidden sm:inline">{time.toLocaleTimeString('en-US', { hour12: false })}</span>
    </div>
  )
}
