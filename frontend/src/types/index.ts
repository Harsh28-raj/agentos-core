export interface Task {
  id: string
  title: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
}

export interface Memory {
  id: string
  content: string
  timestamp: string
}
