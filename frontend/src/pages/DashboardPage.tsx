import { ChatPanel } from '../components/dashboard/ChatPanel'
import { ToolStatus } from '../components/dashboard/ToolStatus'
import { TaskBoard } from '../components/dashboard/TaskBoard'
import { MemoryViewer } from '../components/dashboard/MemoryViewer'

export default function DashboardPage() {
  return (
    <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 lg:p-6 w-full max-w-[1600px] mx-auto">
      <div className="lg:col-span-8 flex flex-col min-h-[500px]">
        <ChatPanel />
      </div>
      <div className="lg:col-span-4 flex flex-col gap-4 overflow-visible">
        <ToolStatus />
        <TaskBoard />
        <MemoryViewer />
      </div>
    </div>
  )
}
