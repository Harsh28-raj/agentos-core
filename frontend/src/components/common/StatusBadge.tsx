export function StatusBadge({ status }: { status: string }) {
    const getStatusColor = (s: string) => {
    switch (s) {
      case 'completed':
        return 'bg-emerald-950/50 text-emerald-400 border-emerald-800/60'
      case 'in_progress':
        return 'bg-amber-950/50 text-amber-400 border-amber-800/60 animate-pulse'
      case 'failed':
        return 'bg-rose-950/50 text-rose-400 border-rose-800/60'
      default:
        return 'bg-neutral-900 text-neutral-400 border-neutral-800'
    }
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider border ${getStatusColor(status)}`}>
      {status.replace('_', ' ')}
    </span>
  )
}
