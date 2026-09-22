import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { EmptyState, ErrorState, Skeleton } from '../components/Common'
import Icon from '../components/Icon'
import { useCategoryInfo } from '../components/SchemeCard'
import { useCatalog } from '../hooks/useCatalog'
import { pick, useLang } from '../i18n'
import { Link, withQuery } from '../router'

function Body({ scheme }) {
  const { lang, t } = useLang()
  const { label, icon } = useCategoryInfo(scheme)
  const name = pick(scheme.name, lang)
  const blocks = [
    { key: 'who', icon: 'check-circle', text: pick(scheme.eligibility, lang) },
    { key: 'get', icon: 'doc', text: pick(scheme.benefits, lang) },
    { key: 'how', icon: 'arrow-right', text: pick(scheme.how_to_apply, lang) },
  ]

  return (
    <div className="wrap detail">
      <Link to="/schemes" className="back-link"><Icon name="arrow-left" size={16} /> {t('detail.back')}</Link>

      <div className="detail-grid">
        <article className="detail-main">
          <span className="tag"><Icon name={icon} size={16} /> {label}</span>
          <h1>{name}</h1>
          <p className="lede">{pick(scheme.description, lang)}</p>
          <p className="dept">{t('schemes.department')}: <strong>{scheme.department}</strong></p>

          {blocks.map((b) => (
            <section key={b.key} className="fact">
              <h2><Icon name={b.icon} size={20} /> {t(`detail.${b.key}`)}</h2>
              <p>{b.text}</p>
            </section>
          ))}

          <p className="callout"><Icon name="info" size={18} /> {t('detail.confirm')}</p>
        </article>

        <aside className="detail-side">
          <Link to={withQuery('/assistant', { q: t('detail.askQuery', { name }) })} className="btn btn-primary btn-block">
            <Icon name="chat" size={18} /> {t('detail.ask')}
          </Link>
          <Link to="/eligibility" className="btn btn-quiet btn-block">
            <Icon name="check-circle" size={18} /> {t('detail.check')}
          </Link>
          {scheme.official_link && (
            <a href={scheme.official_link} target="_blank" rel="noopener noreferrer" className="btn btn-quiet btn-block">
              <Icon name="external" size={18} /> {t('detail.website')}
            </a>
          )}
        </aside>
      </div>
    </div>
  )
}

export default function SchemeDetail({ id }) {
  const { t } = useLang()
  const catalog = useCatalog()
  const fromCatalog = catalog.schemes.find((s) => s.id === id)
  const [state, setState] = useState({ status: fromCatalog ? 'ready' : 'loading', scheme: fromCatalog })

  useEffect(() => {
    if (fromCatalog) { setState({ status: 'ready', scheme: fromCatalog }); return undefined }
    let cancelled = false
    setState({ status: 'loading' })
    api.scheme(id)
      .then((scheme) => { if (!cancelled) setState({ status: 'ready', scheme }) })
      .catch((err) => { if (!cancelled) setState({ status: err.status === 404 ? 'missing' : 'error' }) })
    return () => { cancelled = true }
  }, [id, fromCatalog])

  if (state.status === 'loading') return <div className="wrap section-tight"><Skeleton lines={6} /></div>
  if (state.status === 'missing') {
    return (
      <div className="wrap section-tight">
        <EmptyState title={t('detail.notFound')}>
          <Link to="/schemes" className="btn btn-quiet">{t('detail.back')}</Link>
        </EmptyState>
      </div>
    )
  }
  if (state.status === 'error') return <div className="wrap section-tight"><ErrorState message={t('schemes.loadError')} /></div>
  return <Body scheme={state.scheme} />
}
