import { API_BASE_URL as BASE_URL } from '../env'

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function handleResponse(response: Response) {
  if (!response.ok) {
    let message = 'API Error'
    try {
      const data = await response.json()
      if (data.error && data.error.message) {
        message = data.error.message
      }
    } catch {
      // Ignore JSON parse error
    }
    throw new ApiError(response.status, message)
  }
  return response.json()
}

export const apiClient = {
  get: async (endpoint: string, options: RequestInit = {}) => {
    const token = localStorage.getItem('access_token')
    const headers = new Headers(options.headers || {})
    if (token) headers.set('Authorization', `Bearer ${token}`)
    
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    })
    
    // Auto-refresh logic could go here on 401
    
    return handleResponse(response)
  },

  post: async (endpoint: string, body: any, options: RequestInit = {}) => {
    const token = localStorage.getItem('access_token')
    const headers = new Headers(options.headers || {})
    if (token) headers.set('Authorization', `Bearer ${token}`)
    
    const isFormData = body instanceof URLSearchParams || body instanceof FormData
    if (!isFormData) {
      headers.set('Content-Type', 'application/json')
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      method: 'POST',
      headers,
      body: isFormData ? body : JSON.stringify(body),
    })
    
    return handleResponse(response)
  }
}
