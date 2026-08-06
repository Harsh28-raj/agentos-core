import { useEffect, useState } from 'react'
import { SystemStatusBar } from '../system/SystemStatusBar'

export function Hero() {
  const [bootSequence, setBootSequence] = useState<string[]>([])
  
  useEffect(() => {
    const sequence = [
      'Initializing memory...',
      'Connecting tools...',
      'Ready.'
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
      <div className="mb-12 max-w-lg mx-auto bg-surface border border-hairline p-4 rounded-base text-left shadow-sm w-full">
        <SystemStatusBar />
        <div className="mt-4 font-mono text-xs text-slate min-h-16">
          {bootSequence.map((line, i) => (
            <div key={i} className={i === bootSequence.length - 1 ? 'text-signal' : ''}>
              &gt; {line}
            </div>
          ))}
          {bootSequence.length < 3 && <span className="animate-pulse">&gt; _</span>}
        </div>
      </div>
      
      <h1 className="font-display text-5xl md:text-7xl font-bold tracking-tight mb-6 max-w-4xl mx-auto text-ink leading-tight">
        Your life, one command away.
      </h1>
      <p className="font-body text-xl text-slate max-w-2xl mx-auto mb-10">
        AgentOS is a personal operating system built on autonomous agents. It remembers, it reasons, and it executes on your behalf.
      </p>
    </section>
  )
}
