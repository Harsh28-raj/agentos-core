import { ChatPanel } from '../components/dashboard/ChatPanel'
import { ToolStatus } from '../components/dashboard/ToolStatus'
import { TaskBoard } from '../components/dashboard/TaskBoard'
import { MemoryViewer } from '../components/dashboard/MemoryViewer'

export default function DashboardPage() {
  return (
    <div className="h-full grid grid-cols-1 md:grid-cols-12 gap-6 pb-6">
      <div className="col-span-1 md:col-span-8 h-[600px] md:h-full">
        <ChatPanel />
      </div>
      <div className="col-span-1 md:col-span-4 flex flex-col gap-6 h-[600px] md:h-full">
        <div className="flex-1 min-h-0">
          <ToolStatus />
        </div>
        <div className="flex-1 min-h-0">
          <TaskBoard />
        </div>
        <div className="flex-1 min-h-0">
          <MemoryViewer />
        </div>
      </div>
    </div>
  )
}
