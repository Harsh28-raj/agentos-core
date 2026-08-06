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
    if (isTyping || !input.trim()) return

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
    <Card title={<span className="font-mono text-white text-sm">TERMINAL</span>} className="h-full flex flex-col bg-[#0d0d0d] border-neutral-800 text-white transition-colors duration-200">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-slate text-sm font-mono text-center mt-10">
            Awaiting command...
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg p-3 text-sm transition-colors duration-200 ${m.role === 'user' ? 'bg-neutral-800/50 border border-neutral-700/50 text-neutral-200' : 'bg-transparent border-l-2 border-emerald-500 font-mono text-neutral-300'}`}>
              {m.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-transparent border-l-2 border-emerald-500 p-3 text-emerald-500 animate-pulse font-mono text-xs">
              Agent processing...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2 shrink-0 border border-neutral-800 bg-neutral-900/50 rounded-full p-2 items-center w-full mt-auto transition-all focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500/40">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Execute task..."
          className="flex-1 px-4 py-2 bg-transparent text-white outline-none focus:outline-none focus:ring-0 font-mono text-sm placeholder:text-neutral-500"
          disabled={isTyping}
        />
        <button 
          type="submit" 
          disabled={isTyping || !input.trim()}
          className="bg-emerald-500/20 hover:bg-emerald-500 text-emerald-400 hover:text-black p-2 rounded-full transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={16} />
        </button>
      </form>
    </Card>
  )
}
