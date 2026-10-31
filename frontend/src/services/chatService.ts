import { API_BASE_URL } from '../env'
import { ApiError, apiClient, authHeaders, errorMessage } from './apiClient'
import type { ApprovalAction, ChatReply, HistoryResponse, LogEntry, StreamEvent, SystemStatus } from '../types'

export const chatService = {
  history: (threadId: string) => apiClient.get<HistoryResponse>(`/chat/history/${threadId}`),
  clear: (threadId: string) => apiClient.delete<{ status: string }>(`/chat/history/${threadId}`),
  approve: (threadId: string, action: ApprovalAction, updatedArgs?: Record<string, unknown>) =>
    apiClient.post<ChatReply & { status: string }>('/chat/approve', {
      thread_id: threadId,
      action,
      updated_args: updatedArgs,
    }),
  logs: (threadId: string) => apiClient.get<{ logs: LogEntry[] }>(`/logs/${threadId}`),
  systemStatus: () => apiClient.get<SystemStatus>('/system/status'),
  googleStatus: () => apiClient.get<{ configured: boolean; connected: boolean }>('/integrations/google/status'),
  googleAuthorize: () => apiClient.post<{ url: string }>('/integrations/google/authorize'),
  googleDisconnect: () => apiClient.delete<{ connected: boolean }>('/integrations/google'),
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<{ message: string; stored_file: string | null }>('/upload', form)
  },

  /** POST /chat/stream and call `onEvent` for every Server-Sent Event. */
  async stream(threadId: string, message: string, onEvent: (event: StreamEvent) => void): Promise<void> {
    const headers = authHeaders({ 'Content-Type': 'application/json' })
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message, thread_id: threadId }),
    })
    if (!response.ok || !response.body) throw new ApiError(response.status, await errorMessage(response))

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    for (;;) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const frames = buffer.split('\n\n')
      buffer = frames.pop() ?? ''
      for (const frame of frames) {
        const line = frame.split('\n').find((l) => l.startsWith('data: '))
        if (!line) continue
        try {
          onEvent(JSON.parse(line.slice(6)) as StreamEvent)
        } catch {
          // Ignore a malformed frame rather than aborting the whole stream
        }
      }
    }
  },
}
