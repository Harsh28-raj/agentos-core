import { apiClient } from './apiClient'
import type { AuthTokens, User } from '../types/auth'

export const authService = {
  login: async (email: string, password: string): Promise<AuthTokens> => {
    return apiClient.post('/auth/login', { email, password })
  },

  register: async (email: string, password: string): Promise<User> => {
    return apiClient.post('/auth/register', { email, password })
  },

  getMe: async (): Promise<User> => {
    return apiClient.get('/auth/me')
  }
}
