import { useLang } from '../i18n'
import { Link } from '../router'
import { PhulkariBand } from './Phulkari'

export default function Footer() {
  const { t } = useLang()
  return (
    <footer className="site-footer">
      <PhulkariBand height={30} />
      <div className="wrap footer-row">
        <div className="footer-brand">
          <strong>{t('brand')}</strong>
          <p>{t('footer.note')}</p>
        </div>
        <nav className="footer-nav" aria-label={t('footer.explore')}>
          <Link to="/schemes">{t('nav.schemes')}</Link>
          <Link to="/eligibility">{t('nav.eligibility')}</Link>
          <Link to="/assistant">{t('nav.assistant')}</Link>
          <Link to="/about">{t('nav.about')}</Link>
        </nav>
      </div>
    </footer>
  )
}
