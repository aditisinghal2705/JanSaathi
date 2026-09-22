import Icon from '../components/Icon'
import { PageHead } from '../components/Common'
import { LanguageSwitch } from '../components/Header'
import { useLang } from '../i18n'

export default function About() {
  const { t } = useLang()
  const icons = ['doc', 'shield', 'info', 'help']
  return (
    <>
      <PageHead title={t('about.title')} sub={t('about.lead')} />
      <div className="wrap section-tight about">
        <div className="about-grid">
          {t('about.blocks').map((b, i) => (
            <section key={b.t} className="about-block">
              <Icon name={icons[i]} size={24} />
              <h2>{b.t}</h2>
              <p>{b.d}</p>
            </section>
          ))}
        </div>
        <section className="about-lang">
          <Icon name="globe" size={24} />
          <div>
            <h2>{t('about.langTitle')}</h2>
            <p>{t('about.langBody')}</p>
          </div>
          <LanguageSwitch />
        </section>
      </div>
    </>
  )
}
