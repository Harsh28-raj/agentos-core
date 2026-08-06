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
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#0d0d0d] text-white p-4 font-mono transition-colors duration-200">
      <div className="w-full max-w-md bg-neutral-900/50 p-8 rounded-lg border border-neutral-800 shadow-2xl">
        <div className="mb-8 text-center">
          <h1 className="font-mono text-3xl font-bold tracking-tight text-white mb-2">AgentOS</h1>
          <p className="font-mono text-xs text-neutral-400 uppercase tracking-[0.2em]">SYSTEM AUTHENTICATION</p>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
