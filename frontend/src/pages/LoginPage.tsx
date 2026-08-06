import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { authService } from '../services/authService'

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
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-base">
          {error}
        </div>
      )}
      
      <div>
        <label className="block text-xs font-medium text-neutral-400 mb-1.5 font-mono">EMAIL</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-3 py-2 bg-neutral-900 border border-neutral-700 rounded text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 font-mono text-sm transition-all"
          placeholder="system@agentos.local"
        />
      </div>
      
      <div>
        <label className="block text-xs font-medium text-neutral-400 mb-1.5 font-mono">PASSWORD</label>
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-3 py-2 bg-neutral-900 border border-neutral-700 rounded text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 font-mono text-sm transition-all"
        />
      </div>
      
      <button type="submit" disabled={isSubmitting} className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-mono font-bold rounded shadow-[0_0_15px_rgba(16,185,129,0.4)] transition-all disabled:opacity-50">
        {isSubmitting ? 'Authenticating...' : 'Authenticate'}
      </button>

      <div className="text-center mt-6 text-sm text-neutral-500 font-mono">
        New operator? <Link to="/register" className="text-emerald-400 hover:text-emerald-300 hover:underline">Initialize account</Link>
      </div>
    </form>
  )
}
