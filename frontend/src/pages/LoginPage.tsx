import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { authService } from '../services/authService'
import { Mail, Lock } from 'lucide-react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      const tokens = await authService.login(email, password)
      
      // Get user profile right after login to populate context
      localStorage.setItem('access_token', tokens.access_token)
      const user = await authService.getMe()
      
      login(user, tokens.access_token, tokens.refresh_token)
    } catch (err: any) {
      setError(err.message || 'Login failed')
      localStorage.removeItem('access_token')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-3 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg font-mono">
          {error}
        </div>
      )}
      
      <div className="space-y-1.5">
        <label className="block font-mono text-xs text-neutral-300">Email</label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" size={16} />
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full pl-10 pr-3 py-2.5 bg-neutral-900/80 border border-neutral-800 text-white font-mono placeholder:text-neutral-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 rounded-lg transition-all focus:outline-none"
            placeholder="system@agentos.local"
          />
        </div>
      </div>
      
      <div className="space-y-1.5">
        <label className="block font-mono text-xs text-neutral-300">Password</label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" size={16} />
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full pl-10 pr-3 py-2.5 bg-neutral-900/80 border border-neutral-800 text-white font-mono placeholder:text-neutral-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 rounded-lg transition-all focus:outline-none"
            placeholder="••••••••"
          />
        </div>
      </div>
      
      <button 
        type="submit" 
        disabled={isSubmitting}
        className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-400 text-black font-mono font-bold text-xs rounded-lg shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all duration-300 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-2"
      >
        {isSubmitting ? 'AUTHENTICATING...' : 'AUTHENTICATE OPERATOR →'}
      </button>

      <div className="text-center mt-6">
        <Link to="/register" className="font-mono text-xs text-neutral-400 hover:text-emerald-400 transition-colors cursor-pointer">
          New operator? Initialize account
        </Link>
      </div>
    </form>
  )
}
