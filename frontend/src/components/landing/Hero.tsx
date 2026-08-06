import { useEffect, useState } from 'react'
import { SystemStatusBar } from '../system/SystemStatusBar'

export function Hero() {
  const [bootSequence, setBootSequence] = useState<string[]>([])
  
  useEffect(() => {
    const sequence = [
      'Initializing memory...',
      '[1/5] Connecting Web Search tool...',
      '[2/5] Connecting Weather API...',
      '[3/5] Connecting Calculator...',
      '[4/5] Connecting Calendar Agent...',
      '[5/5] Connecting Gmail Agent...',
      'All systems go. Ready.'
    ]
    
    let currentIndex = 0
    const interval = setInterval(() => {
      if (currentIndex < sequence.length) {
        setBootSequence(prev => [...prev, sequence[currentIndex]])
        currentIndex++
      } else {
        clearInterval(interval)
      }
    }, 800)

    return () => clearInterval(interval)
  }, [])

  return (
    <section className="py-24 md:py-32 flex flex-col items-center justify-center text-center px-4">
      <div className="mb-12 max-w-lg mx-auto bg-surface/80 backdrop-blur-sm border border-neutral-800/80 rounded-xl text-left shadow-[0_0_50px_-12px_rgba(16,185,129,0.2)] w-full overflow-hidden">
        <div className="flex items-center px-4 py-2 border-b border-neutral-800/80 bg-neutral-900/60">
          <div className="flex space-x-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          </div>
          <div className="flex-1 text-center font-mono text-[10px] text-neutral-500">
            system_status.log
          </div>
        </div>
        <div className="p-4">
          <SystemStatusBar />
          <div className="mt-4 font-mono text-xs text-slate min-h-[120px]">
            {bootSequence.map((line, i) => (
              <div key={i} className={i === bootSequence.length - 1 ? 'text-emerald-400 mt-2 font-bold' : ''}>
                &gt; {line}
              </div>
            ))}
            {bootSequence.length < 7 && <span className="animate-pulse">&gt; _</span>}
          </div>
        </div>
      </div>
      
      <h1 className="font-display text-5xl md:text-7xl font-bold tracking-tight mb-6 max-w-4xl mx-auto leading-tight bg-gradient-to-b from-white via-neutral-200 to-neutral-500 bg-clip-text text-transparent">
        Your life, <span className="underline decoration-emerald-500/50 underline-offset-8">one command away.</span>
      </h1>
      <p className="font-body text-xl text-slate max-w-2xl mx-auto mb-10">
        AgentOS is a personal operating system built on autonomous agents. It remembers, it reasons, and it executes on your behalf.
      </p>
    </section>
  )
}
