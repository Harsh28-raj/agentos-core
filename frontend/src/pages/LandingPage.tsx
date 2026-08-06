import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Moon, Sun } from 'lucide-react'

export default function LandingPage() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [time, setTime] = useState('')

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [theme])

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }))
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-[#0d0d0d] text-white font-mono flex flex-col transition-colors duration-200 selection:bg-emerald-500/30">
      <header className="px-6 py-4 flex items-center justify-between border-b border-neutral-800 bg-[#0d0d0d]/90 backdrop-blur-md z-50">
        <div className="font-mono font-bold tracking-widest text-lg text-emerald-400">AgentOS</div>
        <div className="flex items-center space-x-6">
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="text-neutral-400 hover:text-emerald-400 focus:outline-none transition-colors"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link to="/login" className="text-sm font-bold uppercase tracking-widest text-white hover:text-emerald-400 transition-colors border border-neutral-700 hover:border-emerald-500 px-4 py-1.5 rounded bg-neutral-900/50 hover:bg-emerald-900/20 shadow-[0_0_10px_rgba(16,185,129,0)] hover:shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            LOGIN
          </Link>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-4xl mx-auto w-full">
        <div className="w-full text-left bg-neutral-900/40 border border-neutral-800 rounded-lg p-5 mb-12 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-emerald-500/0 via-emerald-500 to-emerald-500/0 opacity-50"></div>
          <div className="flex items-center gap-2 text-xs text-neutral-400 mb-4 border-b border-neutral-800/80 pb-3">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]"></span>
            <span>SYSTEM ONLINE | 5 TOOLS ACTIVE | {time || '00:00:00'}</span>
          </div>
          <div className="space-y-2 text-emerald-400/90 text-sm">
            <p>&gt; Initializing memory...</p>
            <p>&gt; Connecting tools...</p>
            <p>&gt; Ready.</p>
          </div>
        </div>

        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6 bg-gradient-to-br from-white to-neutral-400 bg-clip-text text-transparent">
          Your life, one command away.
        </h1>
        <p className="text-base md:text-lg text-neutral-400 max-w-2xl leading-relaxed">
          AgentOS is a personal operating system built on autonomous agents. It remembers, it reasons, and it executes on your behalf.
        </p>
      </main>
    </div>
  )
}
