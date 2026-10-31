import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { authService } from '../services/authService'
import { authInput, authButton, authLink, authMuted } from './authStyles'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login } = useAuth()
  const registered = (useLocation().state as { registered?: boolean } | null)?.registered

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      const res = await authService.login(email, password)
      // AuthLayout redirects to the dashboard as soon as the user is set
      login(res.user, res.access_token)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {registered && !error && (
        <div className="p-3 text-sm text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-base">
          Account created. You can sign in now.
        </div>
      )}
      {error && (
        <div className="p-3 text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-base">{error}</div>
      )}

      <div>
        <label className={`block text-xs font-medium mb-1.5 font-mono ${authMuted}`}>EMAIL</label>
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={authInput} placeholder="system@agentos.local" autoComplete="email" />
      </div>

      <div>
        <label className={`block text-xs font-medium mb-1.5 font-mono ${authMuted}`}>PASSWORD</label>
        <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className={authInput} autoComplete="current-password" />
      </div>

      <button type="submit" disabled={isSubmitting} className={authButton}>
        {isSubmitting ? 'Authenticating...' : 'Authenticate'}
      </button>

      <div className="text-center mt-6 text-sm text-neutral-500 font-mono">
        New operator? <Link to="/register" className={authLink}>Initialize account</Link>
      </div>
    </form>
  )
}
