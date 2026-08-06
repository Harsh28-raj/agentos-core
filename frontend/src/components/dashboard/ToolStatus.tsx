import { Card } from '../common/Card'
import { Globe, CloudSun, Calculator, Calendar, Mail } from 'lucide-react'

export function ToolStatus() {
  const tools = [
    { name: 'Web Search', status: 'ONLINE', icon: Globe },
    { name: 'Weather API', status: 'ONLINE', icon: CloudSun },
    { name: 'Calculator', status: 'ONLINE', icon: Calculator },
    { name: 'Calendar Agent', status: 'ONLINE', icon: Calendar },
    { name: 'Gmail Agent', status: 'ONLINE', icon: Mail },
  ]

  return (
    <Card title="TOOL CONNECTIONS" className="h-full bg-white dark:bg-neutral-900/60 border-slate-200 dark:border-neutral-800/80 text-slate-800 dark:text-neutral-200 transition-colors duration-200">
      <div className="space-y-2.5">
        {tools.map((tool) => (
          <div key={tool.name} className="flex justify-between items-center p-2.5 rounded-lg bg-slate-50 dark:bg-neutral-900/40 border border-slate-200 dark:border-neutral-800/80 hover:bg-slate-100 hover:dark:bg-neutral-900/60 hover:border-slate-300 dark:hover:border-neutral-700 transition-colors duration-200">
            <div className="flex items-center gap-2.5">
              <tool.icon size={14} className="text-emerald-600 dark:text-emerald-500/70" />
              <span className="font-mono text-xs text-slate-600 dark:text-neutral-400">{tool.name}</span>
            </div>
            <div className="bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 text-[10px] font-mono px-2 py-0.5 rounded-full flex items-center gap-1.5 shadow-[0_0_10px_rgba(16,185,129,0.15)]">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {tool.status}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
