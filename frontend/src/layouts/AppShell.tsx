import { Outlet } from 'react-router-dom'
import { SystemStatusBar } from '../components/system/SystemStatusBar'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../theme/useTheme'
import { LogOut, Moon, Sun } from 'lucide-react'

export function AppShell() {
  const { logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="min-h-screen flex flex-col bg-paper text-ink transition-colors duration-200">
      <header className="border-b border-hairline px-6 py-4 flex items-center justify-between shrink-0 bg-surface">
        <SystemStatusBar />
        <div className="flex items-center space-x-6">
          <button
            onClick={toggleTheme}
            className="text-slate hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal rounded-full p-1"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            onClick={logout}
            className="flex items-center space-x-2 text-slate hover:text-ink text-sm font-body focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal rounded p-1"
          >
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </header>
      <main className="flex-1 overflow-hidden p-6">
        <Outlet />
      </main>
    </div>
  )
}
