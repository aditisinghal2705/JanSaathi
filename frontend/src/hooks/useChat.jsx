import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import { ApiError, streamChat } from '../api/client'
import { useLang } from '../i18n'

// Chat state lives above the router so the conversation survives moving between
// pages (for example opening a scheme and coming back). It is in memory only:
// nothing is written to the browser, because chats can contain personal details.
const ChatContext = createContext(null)
let counter = 0
const nextId = () => `m${Date.now()}-${counter++}`
const HISTORY_LIMIT = 20

export function ChatProvider({ children }) {
  const { lang } = useLang()
  const [messages, setMessages] = useState([])
  const [busy, setBusy] = useState(false)
  const abortRef = useRef(null)
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  const patch = useCallback((id, change) => {
    setMessages((list) => list.map((m) => (m.id === id ? { ...m, ...(typeof change === 'function' ? change(m) : change) } : m)))
  }, [])

  const send = useCallback(async (text) => {
    const message = text.trim()
    if (!message || busy) return

    const history = messagesRef.current
      .filter((m) => m.content && !m.error)
      .slice(-HISTORY_LIMIT)
      .map((m) => ({ role: m.role, content: m.content }))

    const assistantId = nextId()
    setMessages((list) => [
      ...list,
      { id: nextId(), role: 'user', content: message },
      { id: assistantId, role: 'assistant', content: '', pending: true, streaming: true, schemes: [], suggestions: [] },
    ])
    setBusy(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      await streamChat(
        { message, language: lang, history },
        {
          signal: controller.signal,
          onMeta: (meta) => patch(assistantId, { schemes: meta.matched_schemes || [], provider: meta.provider }),
          onDelta: (piece) => patch(assistantId, (m) => ({ content: m.content + piece, pending: false })),
          onDone: (done) => patch(assistantId, {
            pending: false,
            streaming: false,
            suggestions: done.suggestions || [],
            provider: done.provider,
            degraded: !!done.degraded,
            interrupted: !!done.interrupted,
          }),
        },
      )
    } catch (err) {
      if (err.name === 'AbortError') return
      const code = err instanceof ApiError && err.status === 429 ? 'rateLimit'
        : err instanceof ApiError && err.status === 0 ? 'offline' : 'error'
      patch(assistantId, (m) => (m.content
        ? { interrupted: true }
        : { error: code }))
    } finally {
      setBusy(false)
      patch(assistantId, { pending: false, streaming: false })
    }
  }, [busy, lang, patch])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setBusy(false)
  }, [])

  const value = useMemo(() => ({ messages, busy, send, reset }), [messages, busy, send, reset])
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used inside <ChatProvider>')
  return ctx
}
