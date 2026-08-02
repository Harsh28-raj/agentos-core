import type { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline'
  fullWidth?: boolean
}

export function Button({ 
  children, 
  variant = 'primary', 
  fullWidth = false, 
  className = '', 
  ...props 
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-base transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal focus-visible:ring-offset-2 focus-visible:ring-offset-paper disabled:opacity-50 disabled:cursor-not-allowed font-body'
  
  const variants = {
    primary: 'bg-signal text-signal-ink hover:bg-opacity-90',
    secondary: 'bg-surface text-ink hover:bg-opacity-80 border border-hairline',
    outline: 'border border-signal text-signal hover:bg-signal hover:text-signal-ink'
  }

  const classes = `${baseStyles} ${variants[variant]} ${fullWidth ? 'w-full' : ''} ${className}`

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  )
}
