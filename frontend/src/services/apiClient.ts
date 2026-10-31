import { API_BASE_URL as BASE_URL } from '../env'

export const TOKEN_KEY = 'access_token'
export const AUTH_LOGOUT_EVENT = 'agentos:logout'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function authHeaders(extra: HeadersInit = {}): Headers {
  const headers = new Headers(extra)
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return headers
}

/** FastAPI errors look like {detail: "..."} or, for validation errors, {detail: [{msg: "..."}]}. */
export async function errorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => (d.msg ?? '').replace(/^Value error, /, '')).join('; ')
    }
  } catch {
    // Not JSON
  }
  return `Request failed (${response.status})`
}

async function request<T>(method: string, endpoint: string, body?: unknown): Promise<T> {
  const headers = authHeaders()
  const isForm = body instanceof FormData || body instanceof URLSearchParams
  if (body !== undefined && !isForm) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers,
    body: body === undefined ? undefined : isForm ? (body as BodyInit) : JSON.stringify(body),
  })
  if (response.status === 401 && getToken() && !endpoint.startsWith('/auth/login')) {
    // Token expired or was revoked: end the session everywhere
    window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT))
  }
  if (!response.ok) throw new ApiError(response.status, await errorMessage(response))
  return response.json() as Promise<T>
}

export const apiClient = {
  get: <T>(endpoint: string) => request<T>('GET', endpoint),
  post: <T>(endpoint: string, body?: unknown) => request<T>('POST', endpoint, body ?? {}),
  delete: <T>(endpoint: string) => request<T>('DELETE', endpoint),
}
