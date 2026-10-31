import { useCallback, useState } from 'react'
import { ChatPanel } from '../components/dashboard/ChatPanel'
import { ToolStatus } from '../components/dashboard/ToolStatus'
import { TaskBoard } from '../components/dashboard/TaskBoard'
import { MemoryViewer } from '../components/dashboard/MemoryViewer'
import { useAuth } from '../hooks/useAuth'
import { useThreadLogs } from '../hooks/useDashboardData'

const threadStorageKey = (userId: string) => `agentos_thread_${userId}`

function newThreadId() {
  return `t_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
}

export default function DashboardPage() {
  const { user } = useAuth()
  const storageKey = threadStorageKey(user?.id ?? 'anonymous')
  const [threadId, setThreadId] = useState(() => localStorage.getItem(storageKey) || 'default')
  const [refreshKey, setRefreshKey] = useState(0)
  const { logs, error } = useThreadLogs(threadId, refreshKey)

  const startNewThread = useCallback(() => {
    const id = newThreadId()
    localStorage.setItem(storageKey, id)
    setThreadId(id)
  }, [storageKey])

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), [])

  return (
    <div className="w-full min-h-screen bg-white dark:bg-[#0d0d0d] text-neutral-900 dark:text-white font-mono p-3 transition-colors duration-200">
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-4 h-full">
        <div className="lg:col-span-7 flex flex-col min-h-[500px]">
          <ChatPanel threadId={threadId} onNewThread={startNewThread} onActivity={refresh} />
        </div>
        <div className="lg:col-span-3 flex flex-col gap-4">
          <div className="flex-1 min-h-0">
            <ToolStatus />
          </div>
          <div className="flex-1 min-h-0">
            <TaskBoard logs={logs} error={error} />
          </div>
          <div className="flex-1 min-h-0">
            <MemoryViewer logs={logs} error={error} />
          </div>
        </div>
      </div>
    </div>
  )
}
