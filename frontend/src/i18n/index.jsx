import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import en from './en'
import pa from './pa'
import hi from './hi'

const DICTS = { en, pa, hi }

export const LANGUAGES = [
  { code: 'en', short: 'EN', label: 'English', speech: 'en-IN' },
  { code: 'pa', short: 'ਪੰ', label: 'ਪੰਜਾਬੀ', speech: 'pa-IN' },
  { code: 'hi', short: 'हि', label: 'हिन्दी', speech: 'hi-IN' },
]

const STORAGE_KEY = 'jansaathi.lang'
const LangContext = createContext(null)

function initialLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && DICTS[saved]) return saved
  } catch { /* storage may be blocked */ }
  const browser = (navigator.language || 'en').slice(0, 2)
  return DICTS[browser] ? browser : 'en'
}

function lookup(dict, path) {
  return path.split('.').reduce((node, key) => (node == null ? undefined : node[key]), dict)
}

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(initialLang)

  useEffect(() => {
    document.documentElement.lang = lang
    document.title = `${DICTS[lang].brand} · ${DICTS[lang].tagline}`
  }, [lang])

  const setLang = useCallback((code) => {
    if (!DICTS[code]) return
    setLangState(code)
    try { localStorage.setItem(STORAGE_KEY, code) } catch { /* ignore */ }
  }, [])

  const value = useMemo(() => {
    const dict = DICTS[lang]
    // t('home.title')  or  t('home.many', { n: 3 })  -> falls back to English, then to the key
    const t = (path, vars) => {
      let value = lookup(dict, path)
      if (value === undefined) value = lookup(DICTS.en, path)
      if (typeof value !== 'string') return value ?? path
      if (!vars) return value
      return value.replace(/\{(\w+)\}/g, (_, k) => (vars[k] !== undefined ? vars[k] : `{${k}}`))
    }
    return { lang, setLang, t, speech: LANGUAGES.find((l) => l.code === lang).speech }
  }, [lang, setLang])

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>
}

export function useLang() {
  const ctx = useContext(LangContext)
  if (!ctx) throw new Error('useLang must be used inside <LangProvider>')
  return ctx
}

/** Pick the current language from a {en, pa, hi} object coming from the API. */
export function pick(field, lang) {
  if (!field) return ''
  return field[lang] || field.en || ''
}
