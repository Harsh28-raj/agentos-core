import { Card } from '../common/Card'
import { XCircle, Loader2 } from 'lucide-react'

export function ToolStatus() {
  const tools = [
    { name: 'Web Search', status: 'ONLINE' },
    { name: 'Weather API', status: 'ONLINE' },
    { name: 'Calculator', status: 'ONLINE' },
    { name: 'Calendar Agent', status: 'ONLINE' },
    { name: 'Gmail Agent', status: 'ONLINE' },
  ]

  return (
    <Card title={<span className="font-mono text-white text-sm">TOOL CONNECTIONS</span>} className="h-full bg-[#0d0d0d] border-neutral-800 text-white transition-colors duration-200">
      <div className="space-y-3">
        {tools.map((tool) => (
          <div key={tool.name} className="flex justify-between items-center p-3 rounded-lg bg-neutral-900/40 border border-neutral-800/80">
            <span className="font-mono text-xs text-neutral-300">{tool.name}</span>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono text-emerald-500 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-900">{tool.status}</span>
              {tool.status === 'ONLINE' && (
                <div className="relative flex h-3 w-3 items-center justify-center">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500 shadow-[0_0_8px_#22c55e]"></span>
                </div>
              )}
              {tool.status === 'OFFLINE' && <XCircle size={14} className="text-red-500" />}
              {tool.status === 'LOADING' && <Loader2 size={14} className="text-signal animate-spin" />}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
