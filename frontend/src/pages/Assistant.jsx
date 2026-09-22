import { useEffect, useRef } from 'react'
import AskBox from '../components/AskBox'
import Icon from '../components/Icon'
import MessageBubble, { Mark } from '../components/MessageBubble'
import { useCatalog } from '../hooks/useCatalog'
import { useChat } from '../hooks/useChat'
import { useSpeechSynthesis } from '../hooks/useSpeech'
import { useLang } from '../i18n'
import { navigate } from '../router'

export default function Assistant({ params }) {
  const { t, speech: speechLang } = useLang()
  const { messages, busy, send, reset } = useChat()
  const { health } = useCatalog()
  const speech = useSpeechSynthesis(speechLang)
  const scroller = useRef(null)
  const consumed = useRef('')

  // A question handed over from the home page or a scheme page: #/assistant?q=...
  const incoming = params.get('q')
  useEffect(() => {
    if (!incoming) { consumed.current = ''; return }
    if (consumed.current === incoming) return
    consumed.current = incoming
    navigate('/assistant', { replace: true })
    send(incoming)
  }, [incoming, send])

  // keep the newest text in view
  useEffect(() => {
    const el = scroller.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const last = messages[messages.length - 1]
  const asked = new Set(messages.filter((m) => m.role === 'user').map((m) => m.content))
  const suggestions = (last?.suggestions || []).filter((s) => !asked.has(s))
  const showSuggestions = last && last.role === 'assistant' && !busy && suggestions.length > 0
  const demo = health && !health.ai_ready

  return (
    <div className="assistant">
      <aside className="rail">
        <h1>{t('chat.title')}</h1>
        <button type="button" className="btn btn-quiet btn-block" onClick={reset} disabled={messages.length === 0}>
          <Icon name="plus" size={18} /> {t('chat.newChat')}
        </button>
        <h2 className="rail-label">{t('chat.topics')}</h2>
        <ul className="rail-topics">
          {t('home.topics').map((topic) => (
            <li key={topic.label}>
              <button type="button" onClick={() => send(topic.q)} disabled={busy}>{topic.label}</button>
            </li>
          ))}
        </ul>
        <p className="rail-privacy"><Icon name="shield" size={16} /> {t('chat.privacy')}</p>
      </aside>

      <section className="chat" aria-label={t('chat.title')}>
        <div className="chat-bar">
          <strong>{t('chat.title')}</strong>
          <button type="button" className="chip-btn" onClick={reset} disabled={messages.length === 0}>
            <Icon name="plus" size={16} /> {t('chat.newChat')}
          </button>
        </div>

        <div className="chat-scroll" ref={scroller} aria-live="polite">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <Mark size={52} />
              <h2>{t('chat.emptyTitle')}</h2>
              <p>{t('chat.emptyHint')}</p>
              <div className="chat-empty-topics">
                {t('home.topics').map((topic) => (
                  <button key={topic.label} type="button" className="chip-btn" onClick={() => send(topic.q)}>{topic.label}</button>
                ))}
              </div>
            </div>
          ) : (
            <div className="chat-thread">
              {messages.map((m) => <MessageBubble key={m.id} message={m} speech={speech} />)}
              {showSuggestions && (
                <div className="suggestions">
                  {suggestions.map((s) => (
                    <button key={s} type="button" className="chip-btn" onClick={() => send(s)}>{s}</button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="composer">
          <AskBox onSubmit={send} disabled={busy} autoFocus />
          <p className="fineprint">
            <Icon name="shield" size={14} /> {t('chat.privacy')}
            {demo && <><br />{t('chat.demo')}</>}
          </p>
        </div>
      </section>
    </div>
  )
}
