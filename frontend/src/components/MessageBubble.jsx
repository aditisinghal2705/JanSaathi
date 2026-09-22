import { useState } from 'react'
import { useLang } from '../i18n'
import { useSpeechSynthesis } from '../hooks/useSpeech'
import Icon from './Icon'
import Markdown from './Markdown'
import { SchemeChip } from './SchemeCard'

export function Mark({ size = 30 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <rect width="64" height="64" rx="16" fill="var(--green-700)" />
      <path d="M32 10 54 32 32 54 10 32Z" fill="none" stroke="var(--sarson)" strokeWidth="4.5" />
      <path d="M32 21 43 32 32 43 21 32Z" fill="var(--rani)" />
    </svg>
  )
}

function Typing({ label }) {
  return (
    <span className="typing" role="status" aria-label={label}>
      <i /><i /><i />
    </span>
  )
}

export default function MessageBubble({ message, speech }) {
  const { t } = useLang()
  const [copied, setCopied] = useState(false)

  if (message.role === 'user') {
    return (
      <div className="msg msg-user">
        <div className="bubble">{message.content}</div>
      </div>
    )
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content.replace(/\*\*/g, ''))
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch { /* clipboard blocked */ }
  }

  const speaking = speech.speakingId === message.id
  // Actions and notes appear only once the whole answer has arrived.
  const done = !message.streaming && Boolean(message.content)

  return (
    <div className="msg msg-bot">
      <span className="msg-avatar"><Mark /></span>
      <div className="msg-body">
        <div className="bubble">
          {message.pending && !message.content && (
            <span className="thinking"><Typing label={t('chat.thinking')} />{t('chat.thinking')}</span>
          )}
          {message.content && <Markdown text={message.content} />}
          {message.error && <p className="msg-error">{t(`chat.${message.error}`)}</p>}
        </div>

        {done && message.degraded && !message.interrupted && <p className="msg-note"><Icon name="info" size={15} /> {t('chat.degraded')}</p>}
        {done && message.interrupted && <p className="msg-note"><Icon name="info" size={15} /> {t('chat.interrupted')}</p>}

        {done && message.schemes?.length > 0 && (
          <div className="msg-schemes" aria-label={t('chat.schemesMentioned')}>
            {message.schemes.map((s) => <SchemeChip key={s.id} scheme={s} />)}
          </div>
        )}

        {done && (
          <div className="msg-actions">
            {speech.supported && (
              <button type="button" className="chip-btn" onClick={() => (speaking ? speech.stop() : speech.speak(message.id, message.content))}>
                <Icon name={speaking ? 'stop' : 'speaker'} size={16} /> {speaking ? t('chat.stopSpeaking') : t('chat.listen')}
              </button>
            )}
            <button type="button" className="chip-btn" onClick={copy}>
              <Icon name={copied ? 'check' : 'copy'} size={16} /> {copied ? t('chat.copied') : t('chat.copy')}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
