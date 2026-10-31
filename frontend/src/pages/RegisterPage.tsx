import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'
import { authInput, authButton, authLink, authMuted } from './authStyles'

const MIN_PASSWORD_LENGTH = 8

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await authService.register(email, password)
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-base">{error}</div>
      )}

      <div>
        <label className={`block text-xs font-medium mb-1.5 font-mono ${authMuted}`}>EMAIL</label>
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={authInput} placeholder="system@agentos.local" autoComplete="email" />
      </div>

      <div>
        <label className={`block text-xs font-medium mb-1.5 font-mono ${authMuted}`}>PASSWORD</label>
        <input type="password" required minLength={MIN_PASSWORD_LENGTH} maxLength={72} value={password} onChange={(e) => setPassword(e.target.value)} className={authInput} autoComplete="new-password" />
        <p className="mt-1 text-[11px] font-mono text-neutral-500">At least {MIN_PASSWORD_LENGTH} characters.</p>
      </div>

      <button type="submit" disabled={isSubmitting} className={authButton}>
        {isSubmitting ? 'Initializing...' : 'Initialize'}
      </button>

      <div className="text-center mt-6 text-sm text-neutral-500 font-mono">
        Returning operator? <Link to="/login" className={authLink}>Authenticate</Link>
      </div>
    </form>
  )
}
