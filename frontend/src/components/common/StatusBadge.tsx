export function StatusBadge({ status }: { status: string }) {
  const getStatusColor = (s: string) => {
    switch (s) {
      case 'completed':
        return 'bg-green-500/10 text-green-600 border-green-500/20'
      case 'in_progress':
        return 'bg-signal/10 text-signal border-signal/20'
      case 'failed':
        return 'bg-red-500/10 text-red-600 border-red-500/20'
      default:
        return 'bg-slate/10 text-slate border-slate/20'
    }
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider border ${getStatusColor(status)}`}>
      {status.replace('_', ' ')}
    </span>
  )
}
