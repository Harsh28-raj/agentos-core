import { useEffect, useState } from 'react'

export function SystemStatusBar() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="flex items-center space-x-4 font-mono text-xs uppercase text-slate select-none">
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 rounded-full bg-signal animate-pulse" />
        <span className="font-display font-bold text-signal">SYSTEM ONLINE</span>
      </div>
      <span>|</span>
      <span>3 TOOLS ACTIVE</span>
      <span>|</span>
      <span>{time.toLocaleTimeString('en-US', { hour12: false })}</span>
    </div>
  )
}
