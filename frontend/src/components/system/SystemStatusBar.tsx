import { useEffect, useState } from 'react'

export function SystemStatusBar() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="flex items-center space-x-4 font-mono text-xs uppercase text-slate-500 dark:text-neutral-400 select-none transition-colors duration-200">
      <div className="flex items-center space-x-2">
        <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]" />
        <span className="font-display font-bold text-emerald-500">SYSTEM ONLINE</span>
      </div>
      <span>|</span>
      <span>5 TOOLS ACTIVE</span>
      <span>|</span>
      <span>{time.toLocaleTimeString('en-US', { hour12: false })}</span>
    </div>
  )
}
