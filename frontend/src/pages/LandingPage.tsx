import { Link } from 'react-router-dom'
import { Hero } from '../components/landing/Hero'
import { PhilosophyTable } from '../components/landing/PhilosophyTable'
import { FeatureGrid } from '../components/landing/FeatureGrid'
import { ComparisonTable } from '../components/landing/ComparisonTable'
import { DayInTheLife } from '../components/landing/DayInTheLife'
import { UseCaseGrid } from '../components/landing/UseCaseGrid'
import { ClosingCta } from '../components/landing/ClosingCta'
import { useTheme } from '../theme/useTheme'
import { Moon, Sun } from 'lucide-react'

export default function LandingPage() {
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="min-h-screen bg-paper text-ink transition-colors duration-200 selection:bg-signal selection:text-signal-ink">
      <header className="px-6 py-4 flex items-center justify-between border-b border-hairline sticky top-0 bg-paper/80 backdrop-blur-sm z-50">
        <div className="flex items-center space-x-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]" />
          <div className="font-display font-bold tracking-tight text-lg">AgentOS</div>
        </div>
        <div className="flex items-center space-x-6">
          <button
            onClick={toggleTheme}
            className="text-slate hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal rounded-full p-1"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link to="/login" className="border border-neutral-700 bg-neutral-900/40 text-neutral-300 hover:bg-neutral-800 hover:border-neutral-500 hover:text-white transition-all font-mono text-xs px-3 py-1.5 rounded-base">
            LOGIN &rarr;
          </Link>
        </div>
      </header>

      <main>
        <Hero />
        <PhilosophyTable />
        <FeatureGrid />
        <ComparisonTable />
        <DayInTheLife />
        <UseCaseGrid />
        <ClosingCta />
      </main>

      <footer className="py-8 px-4 text-center border-t border-hairline font-mono text-xs text-neutral-500 opacity-80">
        &copy; {new Date().getFullYear()} AgentOS. All rights reserved.
      </footer>
    </div>
  )
}
