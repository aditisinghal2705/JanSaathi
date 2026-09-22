import { useEffect, useState } from 'react'
import { LANGUAGES, useLang } from '../i18n'
import { Link } from '../router'
import Icon from './Icon'

const NAV = [
  { to: '/', key: 'home', match: (p) => p === '/' },
  { to: '/schemes', key: 'schemes', match: (p) => p.startsWith('/schemes') },
  { to: '/eligibility', key: 'eligibility', match: (p) => p.startsWith('/eligibility') },
  { to: '/assistant', key: 'assistant', match: (p) => p.startsWith('/assistant') },
  { to: '/about', key: 'about', match: (p) => p.startsWith('/about') },
]

function Logo() {
  return (
    <svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true">
      <rect width="64" height="64" rx="14" fill="var(--green-700)" />
      <path d="M32 8 56 32 32 56 8 32Z" fill="none" stroke="var(--sarson)" strokeWidth="4" />
      <path d="M32 19 45 32 32 45 19 32Z" fill="var(--rani)" />
      <path d="M32 27 37 32 32 37 27 32Z" fill="var(--paper)" />
    </svg>
  )
}

export function LanguageSwitch() {
  const { lang, setLang, t } = useLang()
  return (
    <div className="lang-switch" role="group" aria-label={t('langLabel')}>
      {LANGUAGES.map((l) => (
        <button
          key={l.code} type="button" lang={l.code}
          className={l.code === lang ? 'is-active' : ''}
          aria-pressed={l.code === lang} title={l.label}
          onClick={() => setLang(l.code)}
        >
          {l.short}
        </button>
      ))}
    </div>
  )
}

export default function Header({ path }) {
  const { t } = useLang()
  const [open, setOpen] = useState(false)
  useEffect(() => setOpen(false), [path])

  return (
    <header className="site-header">
      <div className="wrap header-row">
        <Link to="/" className="brand" aria-label={t('brand')}>
          <Logo />
          <span className="brand-text">
            <span className="brand-name">{t('brand')}</span>
            <span className="brand-tag">{t('tagline')}</span>
          </span>
        </Link>

        <nav className={`nav ${open ? 'is-open' : ''}`} aria-label="Main">
          {NAV.map((n) => (
            <Link key={n.to} to={n.to} className={n.match(path) ? 'is-current' : ''} aria-current={n.match(path) ? 'page' : undefined}>
              {t(`nav.${n.key}`)}
            </Link>
          ))}
        </nav>

        <div className="header-tools">
          <LanguageSwitch />
          <button
            type="button" className="icon-btn nav-toggle" aria-label={t('menu')}
            aria-expanded={open} onClick={() => setOpen((v) => !v)}
          >
            <Icon name={open ? 'close' : 'menu'} />
          </button>
        </div>
      </div>
    </header>
  )
}
