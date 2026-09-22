import { useCatalog } from '../hooks/useCatalog'
import { pick, useLang } from '../i18n'
import { Link } from '../router'
import Icon from './Icon'

/** Category name + icon for a scheme, in the current language. */
export function useCategoryInfo(scheme) {
  const { lang } = useLang()
  const { categoryOf } = useCatalog()
  const cat = categoryOf(scheme)
  return { label: cat ? pick(cat.name, lang) : scheme.category, icon: cat?.icon || 'doc' }
}

/** Full card for the Schemes list. `scheme` is a full SchemePublic record. */
export function SchemeCard({ scheme }) {
  const { lang, t } = useLang()
  const { label, icon } = useCategoryInfo(scheme)
  return (
    <Link to={`/schemes/${scheme.id}`} className="scheme-card">
      <span className="scheme-card-icon"><Icon name={icon} size={22} /></span>
      <span className="scheme-card-cat">{label}</span>
      <h3>{pick(scheme.name, lang)}</h3>
      <p>{pick(scheme.description, lang)}</p>
      <span className="scheme-card-foot">
        <span className="scheme-card-dept">{scheme.department}</span>
        <span className="link-arrow">{t('schemes.open')} <Icon name="arrow-right" size={16} /></span>
      </span>
    </Link>
  )
}

/** Compact chip used under chat answers. `scheme` is a SchemeSummary. */
export function SchemeChip({ scheme }) {
  const { t } = useLang()
  const { label, icon } = useCategoryInfo(scheme)
  return (
    <Link to={`/schemes/${scheme.id}`} className="scheme-chip">
      <span className="scheme-chip-icon"><Icon name={icon} size={18} /></span>
      <span className="scheme-chip-text">
        <strong>{scheme.name}</strong>
        <small>{label}</small>
      </span>
      <span className="scheme-chip-go" aria-label={t('chat.viewScheme')}><Icon name="arrow-right" size={16} /></span>
    </Link>
  )
}
