import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import type { User } from '../types/auth'
import { authService } from '../services/authService'
import { AUTH_LOGOUT_EVENT, TOKEN_KEY } from '../services/apiClient'
import { AuthContext } from './authContextValue'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem('refresh_token') // left behind by older versions
    setUser(null)
  }, [])

  useEffect(() => {
    const initAuth = async () => {
      if (localStorage.getItem(TOKEN_KEY)) {
        try {
          setUser(await authService.getMe())
        } catch {
          logout()
        }
      }
      setIsLoading(false)
    }
    initAuth()
  }, [logout])

  useEffect(() => {
    // apiClient fires this when any request comes back 401
    window.addEventListener(AUTH_LOGOUT_EVENT, logout)
    return () => window.removeEventListener(AUTH_LOGOUT_EVENT, logout)
  }, [logout])

  const login = useCallback((nextUser: User, accessToken: string) => {
    localStorage.setItem(TOKEN_KEY, accessToken)
    setUser(nextUser)
  }, [])

  return <AuthContext.Provider value={{ user, isLoading, login, logout }}>{children}</AuthContext.Provider>
}
