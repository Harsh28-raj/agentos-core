import { apiClient } from './apiClient'
import type { LoginResponse, User } from '../types/auth'

export const authService = {
  login: (email: string, password: string) => apiClient.post<LoginResponse>('/auth/login', { email, password }),
  register: (email: string, password: string) => apiClient.post<{ user: User }>('/auth/register', { email, password }),
  getMe: () => apiClient.get<User>('/auth/me'),
}
