import { useEffect, useRef, useState } from 'react'
import { useLang } from '../i18n'
import { useSpeechRecognition } from '../hooks/useSpeech'
import Icon from './Icon'

/**
 * Text box with voice input. Used as the hero question box on the home page
 * (variant="hero") and as the message composer on the assistant page.
 */
export default function AskBox({ onSubmit, disabled = false, variant = 'composer', placeholder, submitLabel, autoFocus = false }) {
  const { t, speech } = useLang()
  const [text, setText] = useState('')
  const [notice, setNotice] = useState('')
  const area = useRef(null)
  const { supported, listening, start, stop } = useSpeechRecognition(speech)

  // grow with content, up to a limit
  useEffect(() => {
    const el = area.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, variant === 'hero' ? 140 : 160)}px`
  }, [text, variant])

  useEffect(() => { if (autoFocus) area.current?.focus() }, [autoFocus])

  const submit = () => {
    const value = text.trim()
    if (!value || disabled) return
    if (listening) stop()
    onSubmit(value)
    setText('')
  }

  const onKey = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  const toggleMic = () => {
    setNotice('')
    if (!supported) { setNotice(t('chat.micUnsupported')); return }
    if (listening) { stop(); return }
    const base = text ? `${text.trim()} ` : ''
    start((spoken) => setText(base + spoken))
  }

  return (
    <div className={`askbox askbox-${variant}`}>
      <div className={`askbox-field ${listening ? 'is-listening' : ''}`}>
        <textarea
          ref={area} rows={1} value={text} maxLength={1000}
          onChange={(e) => setText(e.target.value)} onKeyDown={onKey}
          placeholder={listening ? t('chat.listening') : (placeholder || t('chat.placeholder'))}
          aria-label={placeholder || t('chat.placeholder')}
        />
        <button
          type="button" className={`icon-btn mic ${listening ? 'is-on' : ''}`}
          onClick={toggleMic} aria-pressed={listening}
          aria-label={listening ? t('chat.stopListening') : t('chat.mic')}
          title={listening ? t('chat.stopListening') : t('chat.mic')}
        >
          <Icon name={listening ? 'stop' : 'mic'} size={20} />
        </button>
        <button type="button" className="btn btn-primary askbox-send" onClick={submit} disabled={disabled || !text.trim()}>
          <span className="askbox-send-label">{submitLabel || t('chat.send')}</span>
          <Icon name="send" size={18} />
        </button>
      </div>
      {notice && <p className="askbox-notice" role="status">{notice}</p>}
    </div>
  )
}
