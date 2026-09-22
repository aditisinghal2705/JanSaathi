import { EmptyState } from '../components/Common'
import { useLang } from '../i18n'
import { Link } from '../router'

export default function NotFound() {
  const { t } = useLang()
  return (
    <div className="wrap section-tight">
      <EmptyState title={t('notFound.title')} hint={t('notFound.body')}>
        <Link to="/" className="btn btn-primary">{t('notFound.home')}</Link>
      </EmptyState>
    </div>
  )
}
