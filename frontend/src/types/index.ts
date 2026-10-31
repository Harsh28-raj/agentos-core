export type ApprovalAction = 'CONFIRM' | 'REJECT' | 'EDIT'

/** Payload of the tool's interrupt(): what is waiting for approval. */
export interface InterruptData {
  tool?: string
  action?: string
  message?: string
  [key: string]: unknown
}

export interface ChatReply {
  reply: string
  hitl_interrupt?: boolean
  interrupt_data?: InterruptData
  pending_count?: number
  error?: boolean
}

export interface HistoryResponse {
  history: { role: 'user' | 'assistant'; content: string }[]
  pending: ChatReply | null
}

export type StreamEvent =
  | { type: 'thinking' | 'error'; content: string }
  | { type: 'route'; content: string; agent: string }
  | { type: 'tool_start'; tool: string; content: string; input: unknown }
  | { type: 'tool_end'; tool: string; content: string; output: string }
  | { type: 'token'; content: string }
  | { type: 'hitl_pause'; content: string; tool?: string; pending_args: InterruptData; pending_count?: number }
  | { type: 'done'; reply: string; tokens: { input: number; output: number; total: number } }

export interface LogEntry {
  id: number
  run_id: string
  tool_name: string | null
  tool_input: unknown
  tool_output: { output?: string } | null
  status: string
  action_taken: string | null
  original_args: Record<string, unknown> | null
  modified_args: Record<string, unknown> | null
  human_feedback: string | null
  created_at: string | null
}

export interface ToolInfo {
  name: string
  status: 'ONLINE' | 'OFFLINE'
  detail: string
}

export interface SystemStatus {
  llm: { status: 'ONLINE' | 'OFFLINE'; model: string }
  checkpointer: string
  tools: ToolInfo[]
  active_tools: number
}
