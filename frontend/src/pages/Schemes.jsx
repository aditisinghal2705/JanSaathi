import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { EmptyState, ErrorState, PageHead, Skeleton } from '../components/Common'
import Icon from '../components/Icon'
import { SchemeCard } from '../components/SchemeCard'
import { useCatalog } from '../hooks/useCatalog'
import { pick, useLang } from '../i18n'
import { navigate, withQuery } from '../router'

export default function Schemes({ params }) {
  const { lang, t } = useLang()
  const catalog = useCatalog()
  const category = params.get('category') || ''
  const [query, setQuery] = useState(params.get('q') || '')
  const [debounced, setDebounced] = useState(query)
  const [result, setResult] = useState({ status: 'idle', items: [] })

  useEffect(() => {
    const id = setTimeout(() => setDebounced(query.trim()), 250)
    return () => clearTimeout(id)
  }, [query])

  const filtered = Boolean(category || debounced)

  useEffect(() => {
    if (catalog.status === 'error') { setResult({ status: 'error', items: [] }); return undefined }
    if (catalog.status !== 'ready') return undefined
    if (!filtered) { setResult({ status: 'ready', items: catalog.schemes }); return undefined }

    let cancelled = false
    setResult((r) => ({ ...r, status: 'loading' }))
    api.schemes({ category, search: debounced })
      .then((data) => { if (!cancelled) setResult({ status: 'ready', items: data.results }) })
      .catch(() => { if (!cancelled) setResult({ status: 'error', items: [] }) })
    return () => { cancelled = true }
  }, [catalog.status, catalog.schemes, category, debounced, filtered])

  const setCategory = (id) => navigate(withQuery('/schemes', id ? { category: id } : {}))
  const clear = () => { setQuery(''); navigate('/schemes') }

  return (
    <>
      <PageHead title={t('schemes.title')} sub={t('schemes.sub')}>
        <div className="search-field">
          <Icon name="search" size={20} />
          <input
            type="search" value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder={t('schemes.search')} aria-label={t('schemes.search')}
          />
        </div>
        <div className="filter-row" role="group" aria-label={t('categories')}>
          <button type="button" className={`filter ${!category ? 'is-active' : ''}`} onClick={() => setCategory('')}>{t('schemes.all')}</button>
          {catalog.categories.map((c) => (
            <button key={c.id} type="button" className={`filter ${category === c.id ? 'is-active' : ''}`} onClick={() => setCategory(c.id)}>
              {pick(c.name, lang)}
            </button>
          ))}
        </div>
      </PageHead>

      <div className="wrap section-tight">
        {result.status === 'error' && <ErrorState message={t('schemes.loadError')} onRetry={catalog.reload} />}
        {(result.status === 'loading' || (result.status === 'idle')) && (
          <div className="card-grid">{[0, 1, 2].map((i) => <Skeleton key={i} lines={4} className="scheme-skeleton" />)}</div>
        )}
        {result.status === 'ready' && (
          <>
            <p className="result-count" role="status">
              {result.items.length === 1 ? t('schemes.resultOne') : t('schemes.results', { n: result.items.length })}
            </p>
            {result.items.length === 0 ? (
              <EmptyState title={t('schemes.none')} hint={t('schemes.noneHint')}>
                <button type="button" className="btn btn-quiet" onClick={clear}>{t('schemes.clear')}</button>
              </EmptyState>
            ) : (
              <div className="card-grid">{result.items.map((s) => <SchemeCard key={s.id} scheme={s} />)}</div>
            )}
          </>
        )}
      </div>
    </>
  )
}
