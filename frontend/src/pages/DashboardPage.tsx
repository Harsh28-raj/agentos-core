import { ChatPanel } from '../components/dashboard/ChatPanel'
import { ToolStatus } from '../components/dashboard/ToolStatus'
import { TaskBoard } from '../components/dashboard/TaskBoard'
import { MemoryViewer } from '../components/dashboard/MemoryViewer'

export default function DashboardPage() {
  return (
    <div className="w-full min-h-screen bg-[#0a0a0a] text-white font-mono p-3">
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-4 h-full">
        <div className="lg:col-span-7 flex flex-col min-h-[500px]">
          <ChatPanel />
        </div>
        <div className="lg:col-span-3 flex flex-col gap-4 overflow-visible">
          <ToolStatus />
          <TaskBoard />
          <MemoryViewer />
        </div>
      </div>
    </div>
  )
}
