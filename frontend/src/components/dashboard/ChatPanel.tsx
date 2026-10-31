import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Paperclip, Plus, Send, Trash2 } from 'lucide-react'
import { Card } from '../common/Card'
import { ApprovalCard } from './ApprovalCard'
import { chatService } from '../../services/chatService'
import type { ApprovalAction, ChatReply, InterruptData, StreamEvent } from '../../types'
import { muted, panel, panelTitle } from './styles'

interface Message {
  id: string
  role: 'user' | 'agent' | 'system'
  content: string
}

interface Pending {
  data: InterruptData
  count: number
}

interface Props {
  threadId: string
  onNewThread: () => void
  onActivity: () => void
}

let nextId = 0
const msg = (role: Message['role'], content: string): Message => ({ id: `${Date.now()}-${nextId++}`, role, content })

export function ChatPanel({ threadId, onNewThread, onActivity }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [pending, setPending] = useState<Pending | null>(null)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status, pending])

  // Load the stored conversation (and any action still waiting for approval)
  useEffect(() => {
    let cancelled = false
    setMessages([])
    setPending(null)
    chatService
      .history(threadId)
      .then((res) => {
        if (cancelled) return
        setMessages(res.history.map((h) => msg(h.role === 'user' ? 'user' : 'agent', h.content)))
        if (res.pending?.interrupt_data) setPending({ data: res.pending.interrupt_data, count: res.pending.pending_count ?? 1 })
      })
      .catch(() => {
        if (!cancelled) setMessages([msg('system', 'Could not load history. Is the backend running?')])
      })
    return () => {
      cancelled = true
    }
  }, [threadId])

  const applyReply = useCallback((reply: ChatReply) => {
    setMessages((prev) => [...prev, msg('agent', reply.reply)])
    setPending(reply.hitl_interrupt && reply.interrupt_data ? { data: reply.interrupt_data, count: reply.pending_count ?? 1 } : null)
  }, [])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (busy || !text) return

    setMessages((prev) => [...prev, msg('user', text)])
    setInput('')
    setBusy(true)
    setStatus('Thinking...')
    let streamed = ''
    const agentMsg = msg('agent', '')

    const onEvent = (event: StreamEvent) => {
      switch (event.type) {
        case 'thinking':
        case 'route':
        case 'tool_start':
          setStatus(event.content)
          break
        case 'token':
          streamed += event.content
          setMessages((prev) => {
            const rest = prev.filter((m) => m.id !== agentMsg.id)
            return [...rest, { ...agentMsg, content: streamed }]
          })
          break
        case 'hitl_pause':
          setMessages((prev) => [...prev.filter((m) => m.id !== agentMsg.id), msg('agent', event.content)])
          setPending({ data: event.pending_args, count: event.pending_count ?? 1 })
          break
        case 'done':
          // The final answer replaces the live tokens (which can include intermediate agent steps)
          setMessages((prev) => [...prev.filter((m) => m.id !== agentMsg.id), { ...agentMsg, content: event.reply }])
          setPending(null)
          break
        case 'error':
          setMessages((prev) => [...prev.filter((m) => m.id !== agentMsg.id), msg('system', event.content)])
          break
      }
    }

    try {
      await chatService.stream(threadId, text, onEvent)
    } catch (err) {
      setMessages((prev) => [...prev, msg('system', err instanceof Error ? err.message : 'Connection failed. Is the backend running?')])
    } finally {
      setBusy(false)
      setStatus('')
      onActivity()
    }
  }

  const decide = async (action: ApprovalAction, updatedArgs?: Record<string, unknown>) => {
    setBusy(true)
    setStatus(action === 'REJECT' ? 'Cancelling...' : 'Executing approved action...')
    try {
      applyReply(await chatService.approve(threadId, action, updatedArgs))
    } catch (err) {
      setMessages((prev) => [...prev, msg('system', err instanceof Error ? err.message : 'Approval failed')])
    } finally {
      setBusy(false)
      setStatus('')
      onActivity()
    }
  }

  const clear = async () => {
    if (busy || !window.confirm('Delete this conversation?')) return
    try {
      await chatService.clear(threadId)
      setMessages([])
      setPending(null)
      onActivity()
    } catch (err) {
      setMessages((prev) => [...prev, msg('system', err instanceof Error ? err.message : 'Could not clear history')])
    }
  }

  const upload = async (file: File | undefined) => {
    if (!file) return
    setBusy(true)
    setStatus(`Uploading ${file.name}...`)
    try {
      const res = await chatService.upload(file)
      const stored = res.stored_file ? ` Ask the vision agent about it using the name ${res.stored_file}.` : ''
      setMessages((prev) => [...prev, msg('system', `📎 ${res.message}${stored}`)])
    } catch (err) {
      setMessages((prev) => [...prev, msg('system', err instanceof Error ? err.message : 'Upload failed')])
    } finally {
      setBusy(false)
      setStatus('')
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const headerButton = 'p-1.5 rounded text-neutral-500 hover:text-emerald-500 disabled:opacity-40'
  return (
    <Card
      title={<span className={panelTitle}>TERMINAL</span>}
      className={`${panel} flex flex-col`}
      headerAction={
        <div className="flex items-center gap-1">
          <button className={headerButton} onClick={onNewThread} disabled={busy} title="New conversation" aria-label="New conversation">
            <Plus size={16} />
          </button>
          <button className={headerButton} onClick={clear} disabled={busy} title="Delete conversation" aria-label="Delete conversation">
            <Trash2 size={16} />
          </button>
        </div>
      }
    >
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && !pending && (
          <div className={`${muted} text-sm font-mono text-center mt-10`}>Awaiting command...</div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-lg p-3 text-sm whitespace-pre-wrap break-words transition-colors duration-200 ${
                m.role === 'user'
                  ? 'bg-neutral-100 dark:bg-neutral-800/50 border border-neutral-200 dark:border-neutral-700/50 text-neutral-800 dark:text-neutral-200'
                  : m.role === 'system'
                    ? 'border-l-2 border-amber-500 font-mono text-xs text-amber-700 dark:text-amber-400'
                    : 'border-l-2 border-emerald-500 font-mono text-neutral-700 dark:text-neutral-300'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {pending && <ApprovalCard key={JSON.stringify(pending.data)} data={pending.data} pendingCount={pending.count} busy={busy} onDecide={decide} />}
        {status && (
          <div className="border-l-2 border-emerald-500 p-3 text-emerald-600 dark:text-emerald-500 animate-pulse font-mono text-xs">{status}</div>
        )}
        <div ref={bottomRef} />
      </div>
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 shrink-0 border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900/50 rounded-full p-2 items-center w-full mt-auto transition-all focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500/40"
      >
        <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" className="hidden" onChange={(e) => upload(e.target.files?.[0])} />
        <button type="button" onClick={() => fileRef.current?.click()} disabled={busy} className="p-2 rounded-full text-neutral-500 hover:text-emerald-500 disabled:opacity-40" aria-label="Upload a PDF or image">
          <Paperclip size={16} />
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={pending ? 'Reply "yes" / "no", or use the buttons above...' : 'Execute task...'}
          className="flex-1 px-2 py-2 bg-transparent text-neutral-900 dark:text-white outline-none focus:outline-none focus:ring-0 font-mono text-sm placeholder:text-neutral-500"
          disabled={busy}
          maxLength={8000}
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="bg-emerald-500/20 hover:bg-emerald-500 text-emerald-600 dark:text-emerald-400 hover:text-black p-2 rounded-full transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Send"
        >
          <Send size={16} />
        </button>
      </form>
    </Card>
  )
}
