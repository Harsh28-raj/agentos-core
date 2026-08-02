import { Card } from '../common/Card'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

export function ToolStatus() {
  const tools = [
    { name: 'Calculator', status: 'online' },
    { name: 'Web Search', status: 'online' },
    { name: 'Code Interpreter', status: 'loading' },
    { name: 'Weather API', status: 'offline' },
  ]

  return (
    <Card title="Tool Connections" className="h-full">
      <div className="space-y-3">
        {tools.map((tool) => (
          <div key={tool.name} className="flex justify-between items-center p-3 rounded-base bg-surface border border-hairline">
            <span className="font-mono text-sm">{tool.name}</span>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono uppercase text-slate tracking-wider">{tool.status}</span>
              {tool.status === 'online' && <CheckCircle size={14} className="text-green-500" />}
              {tool.status === 'offline' && <XCircle size={14} className="text-red-500" />}
              {tool.status === 'loading' && <Loader2 size={14} className="text-signal animate-spin" />}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
