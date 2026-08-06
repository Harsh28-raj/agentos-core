import { Outlet } from 'react-router-dom'
import { SystemStatusBar } from '../components/system/SystemStatusBar'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../theme/useTheme'
import { LogOut, Moon, Sun } from 'lucide-react'

export function AppShell() {
  const { logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="min-h-screen w-full bg-slate-100 dark:bg-neutral-950 text-slate-900 dark:text-neutral-200 flex flex-col overflow-y-auto transition-colors duration-200">
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-neutral-950/90 backdrop-blur-md border-b border-slate-200 dark:border-neutral-800/80 shrink-0 px-6 py-4 flex items-center justify-between transition-colors duration-200">
        <SystemStatusBar />
        <div className="flex items-center space-x-6">
          <button 
            onClick={toggleTheme} 
            className="p-2 rounded-lg hover:bg-neutral-800/50 dark:hover:bg-neutral-800 transition-colors text-amber-400 dark:text-neutral-400"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400"/> : <Moon className="w-4 h-4 text-indigo-600"/>}
          </button>
          <button
            onClick={logout}
            className="flex items-center space-x-2 text-slate-500 dark:text-neutral-400 hover:text-rose-500 dark:hover:text-rose-400 font-mono text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 rounded p-1"
          >
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </header>
      <main className="flex-1 flex flex-col w-full">
        <Outlet />
      </main>
    </div>
  )
}
