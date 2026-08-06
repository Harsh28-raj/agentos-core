import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'
import { Button } from '../components/common/Button'

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
      navigate('/login')
    } catch (err: any) {
      setError(err.message || 'Registration failed')
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
        {isSubmitting ? 'Initializing...' : 'Initialize'}
      </Button>

      <div className="text-center mt-4 text-sm text-slate">
        Returning operator? <Link to="/login" className="text-signal hover:underline">Authenticate</Link>
      </div>
    </form>
  )
}
