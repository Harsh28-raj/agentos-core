import { Outlet, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export function AuthLayout() {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  const isLogin = location.pathname === '/login'

  const windowTitle = isLogin ? 'system_auth_gate.sh' : 'operator_init_protocol.sh'
  const subtitle = isLogin ? '[ SYSTEM AUTHENTICATION ]' : '[ OPERATOR REGISTRATION ]'
  const subtitleColor = isLogin ? 'text-neutral-400' : 'text-emerald-400/80'

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center bg-paper text-ink">Loading...</div>
  }

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-paper text-ink p-4 transition-colors duration-200">
      <div className="w-full max-w-md bg-neutral-950/80 border border-neutral-800 rounded-xl shadow-[0_0_50px_-15px_rgba(16,185,129,0.2)] overflow-hidden">
        {/* Terminal Header */}
        <div className="flex items-center px-4 py-2 border-b border-neutral-800/80 bg-neutral-900/60">
          <div className="flex space-x-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
          </div>
          <div className="flex-1 text-center font-mono text-[10px] text-neutral-500">
            {windowTitle}
          </div>
        </div>
        
        <div className="p-8">
          <div className="mb-8 text-center flex flex-col items-center">
            <div className="flex items-center space-x-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]" />
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">AgentOS</h1>
            </div>
            <p className={`font-mono text-xs mt-2 uppercase tracking-widest ${subtitleColor}`}>
              {subtitle}
            </p>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
