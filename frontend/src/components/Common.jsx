import { useLang } from '../i18n'
import Icon from './Icon'

export function ErrorState({ message, onRetry }) {
  const { t } = useLang()
  return (
    <div className="state" role="alert">
      <Icon name="info" size={28} />
      <p>{message}</p>
      {onRetry && <button type="button" className="btn btn-quiet" onClick={onRetry}>{t('schemes.retry')}</button>}
    </div>
  )
}

export function EmptyState({ title, hint, children }) {
  return (
    <div className="state">
      <Icon name="search" size={28} />
      <h3>{title}</h3>
      {hint && <p>{hint}</p>}
      {children}
    </div>
  )
}

export function Skeleton({ lines = 3, className = '' }) {
  return (
    <div className={`skeleton ${className}`} aria-hidden="true">
      {Array.from({ length: lines }, (_, i) => <span key={i} style={{ width: `${100 - i * 14}%` }} />)}
    </div>
  )
}

export function PageHead({ title, sub, children }) {
  return (
    <div className="page-head">
      <div className="wrap">
        <h1>{title}</h1>
        {sub && <p className="lede">{sub}</p>}
        {children}
      </div>
    </div>
  )
}
