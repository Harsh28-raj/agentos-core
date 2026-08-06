import { Outlet, Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export function AuthLayout() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center bg-paper text-ink">Loading...</div>
  }

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-paper text-ink p-4 transition-colors duration-200">
      <div className="w-full max-w-md bg-surface p-8 rounded-base border border-hairline shadow-sm">
        <div className="mb-8 text-center">
          <h1 className="font-display text-2xl font-bold tracking-tight">AgentOS</h1>
          <p className="font-mono text-xs text-slate mt-2 uppercase tracking-wider">System Authentication</p>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
