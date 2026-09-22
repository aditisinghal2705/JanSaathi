import { useCallback, useEffect, useRef, useState } from 'react'

// Browser speech features. Punjabi and Hindi voice input work in Chrome and Edge
// (Android and desktop). Where a browser or device has no support the buttons
// are hidden or explain why, so nothing breaks. Azure AI Speech can replace
// these later for consistent quality on every device.

const Recognition = typeof window !== 'undefined'
  ? window.SpeechRecognition || window.webkitSpeechRecognition
  : null

export function useSpeechRecognition(speechLang) {
  const [listening, setListening] = useState(false)
  const ref = useRef(null)

  useEffect(() => () => ref.current?.abort?.(), [])

  const stop = useCallback(() => ref.current?.stop?.(), [])

  const start = useCallback((onText) => {
    if (!Recognition) return false
    const rec = new Recognition()
    rec.lang = speechLang
    rec.interimResults = true
    rec.continuous = false
    rec.onresult = (event) => {
      let text = ''
      for (let i = 0; i < event.results.length; i++) text += event.results[i][0].transcript
      onText(text)
    }
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
    ref.current = rec
    try { rec.start(); setListening(true) } catch { setListening(false) }
    return true
  }, [speechLang])

  return { supported: !!Recognition, listening, start, stop }
}

function plain(markdown) {
  return markdown.replace(/\*\*/g, '').replace(/^- /gm, '').replace(/https?:\/\/\S+/g, '')
}

export function useSpeechSynthesis(speechLang) {
  const [speakingId, setSpeakingId] = useState(null)
  const synth = typeof window !== 'undefined' ? window.speechSynthesis : null
  const [hasVoice, setHasVoice] = useState(false)

  useEffect(() => {
    if (!synth) return undefined
    const check = () => {
      const prefix = speechLang.slice(0, 2)
      setHasVoice(synth.getVoices().some((v) => v.lang.toLowerCase().startsWith(prefix)))
    }
    check()
    synth.addEventListener?.('voiceschanged', check)
    return () => synth.removeEventListener?.('voiceschanged', check)
  }, [synth, speechLang])

  useEffect(() => () => synth?.cancel(), [synth])

  const speak = useCallback((id, text) => {
    if (!synth) return
    synth.cancel()
    const utter = new SpeechSynthesisUtterance(plain(text))
    utter.lang = speechLang
    utter.onend = () => setSpeakingId(null)
    utter.onerror = () => setSpeakingId(null)
    setSpeakingId(id)
    synth.speak(utter)
  }, [synth, speechLang])

  const stop = useCallback(() => { synth?.cancel(); setSpeakingId(null) }, [synth])

  return { supported: !!synth && hasVoice, speakingId, speak, stop }
}
