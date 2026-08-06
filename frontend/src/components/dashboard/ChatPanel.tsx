import { useState, useRef, useEffect } from 'react'
import type { FormEvent } from 'react'
import { Card } from '../common/Card'

import { Send } from 'lucide-react'
import { API_BASE_URL } from '../../env'


interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: input, thread_id: 'default_user', user_id: 'default_user' })
      })

      if (!response.ok) throw new Error('Network response was not ok')

      const data = await response.json()
      const reply = data.reply ?? 'No response received.'

      const agentMessage: Message = { id: (Date.now() + 1).toString(), role: 'agent', content: reply }
      setMessages(prev => [...prev, agentMessage])
    } catch (error) {
      setMessages(prev => [
        ...prev, 
        { id: Date.now().toString(), role: 'agent', content: 'Connection failed. Is the backend running?' }
      ])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <Card title={<span className="font-mono text-white text-sm">TERMINAL</span>} className="h-full flex flex-col bg-[#0a0a0a] border-neutral-800 text-white transition-colors duration-200">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-slate text-sm font-mono text-center mt-10">
            Awaiting command...
          </div>
        )}
        {messages.map((m) => {
          const isHITL = m.role === 'agent' && m.content.includes('Awaiting your approval')
          return (
            <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-lg p-3 text-sm transition-colors duration-200 ${m.role === 'user' ? 'bg-slate-100 dark:bg-neutral-800/50 border border-slate-200 dark:border-neutral-700/50 text-slate-800 dark:text-neutral-200' : 'bg-transparent border-l-2 border-emerald-500 font-mono text-slate-700 dark:text-neutral-300'}`}>
                {m.content}
                {isHITL && (
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => {
                        setInput('CONFIRM')
                        setTimeout(() => {
                          const form = document.querySelector('form')
                          if (form) form.requestSubmit()
                        }, 50)
                      }}
                      className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold rounded shadow-[0_0_10px_rgba(16,185,129,0.3)] transition-all hover:scale-105"
                    >
                      CONFIRM
                    </button>
                    <button
                      onClick={() => {
                        setInput('REJECT')
                        setTimeout(() => {
                          const form = document.querySelector('form')
                          if (form) form.requestSubmit()
                        }, 50)
                      }}
                      className="px-4 py-1.5 bg-neutral-800/80 hover:bg-rose-500/20 text-rose-500 border border-rose-500/30 text-xs font-mono rounded transition-colors"
                    >
                      REJECT
                    </button>
                  </div>
                )}
              </div>
            </div>
          )
        })}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-transparent border-l-2 border-emerald-500 p-3 text-emerald-500 animate-pulse font-mono text-xs">
              Agent processing...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2 shrink-0 border border-zinc-800 bg-zinc-900/50 rounded-lg p-2 items-center w-full mt-auto transition-all">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Execute task..."
          className="flex-1 outline-none focus:outline-none focus:ring-0 bg-transparent text-white font-mono text-sm placeholder:text-neutral-500 transition-colors duration-200"
          disabled={isTyping}
        />
        <button 
          type="submit" 
          disabled={isTyping || !input.trim()}
          className="bg-emerald-500/20 hover:bg-emerald-500 text-emerald-400 hover:text-black p-2 rounded-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={16} />
        </button>
      </form>
    </Card>
  )
}
