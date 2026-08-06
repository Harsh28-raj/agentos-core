import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { authService } from '../services/authService'
import { Button } from '../components/common/Button'

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
        <label className="block text-sm font-medium text-slate mb-1">Email</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-3 py-2 bg-paper border border-hairline rounded-base text-ink focus:outline-none focus:ring-2 focus:ring-signal"
          placeholder="system@agentos.local"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-slate mb-1">Password</label>
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-3 py-2 bg-paper border border-hairline rounded-base text-ink focus:outline-none focus:ring-2 focus:ring-signal"
        />
      </div>
      
      <Button type="submit" fullWidth disabled={isSubmitting}>
        {isSubmitting ? 'Authenticating...' : 'Authenticate'}
      </Button>

      <div className="text-center mt-4 text-sm text-slate">
        New operator? <Link to="/register" className="text-signal hover:underline">Initialize account</Link>
      </div>
    </form>
  )
}
