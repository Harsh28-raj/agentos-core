import type { ReactNode } from 'react'

interface CardProps {
  title: string
  children: ReactNode
  className?: string
  headerAction?: ReactNode
}

export function Card({ title, children, className = '', headerAction }: CardProps) {
  return (
    <div className={`flex flex-col bg-surface border border-hairline rounded-base overflow-hidden ${className}`}>
      <div className="px-4 py-3 border-b border-hairline flex items-center justify-between bg-surface">
        <h3 className="font-mono text-xs uppercase tracking-wider text-slate">{title}</h3>
        {headerAction && <div>{headerAction}</div>}
      </div>
      <div className="p-4 flex-1 overflow-auto bg-paper">
        {children}
      </div>
    </div>
  )
}
