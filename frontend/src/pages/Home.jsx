import { PhulkariBand, PhulkariPanel } from '../components/Phulkari'
import AskBox from '../components/AskBox'
import Icon from '../components/Icon'
import Markdown from '../components/Markdown'
import { Mark } from '../components/MessageBubble'
import { Skeleton } from '../components/Common'
import { useCatalog } from '../hooks/useCatalog'
import { pick, useLang } from '../i18n'
import { Link, navigate, withQuery } from '../router'

function ask(q) {
  navigate(withQuery('/assistant', { q }))
}

function Hero() {
  const { t } = useLang()
  return (
    <section className="hero">
      <div className="wrap hero-grid">
        <div className="hero-copy">
          <h1>{t('home.title')}</h1>
          <p className="lede">{t('home.sub')}</p>
          <AskBox variant="hero" onSubmit={ask} placeholder={t('home.placeholder')} submitLabel={t('home.ask')} />
          <div className="topic-row">
            <span className="topic-label">{t('home.popular')}</span>
            {t('home.topics').map((topic) => (
              <button key={topic.label} type="button" className="chip-btn" onClick={() => ask(topic.q)}>
                {topic.label}
              </button>
            ))}
          </div>
        </div>

        <div className="hero-visual" aria-hidden="true">
          <PhulkariPanel />
          <div className="demo-card">
            <span className="demo-tag">{t('home.exampleTag')}</span>
            <div className="msg msg-user"><div className="bubble">{t('home.exampleQ')}</div></div>
            <div className="msg msg-bot">
              <span className="msg-avatar"><Mark size={28} /></span>
              <div className="msg-body"><div className="bubble"><Markdown text={t('home.exampleA')} /></div></div>
            </div>
          </div>
        </div>
      </div>
      <PhulkariBand height={30} />
    </section>
  )
}

function Browse() {
  const { lang, t } = useLang()
  const { categories, status } = useCatalog()
  return (
    <section className="section">
      <div className="wrap">
        <div className="section-head">
          <h2>{t('home.browseTitle')}</h2>
          <p>{t('home.browseSub')}</p>
        </div>
        {status === 'loading' && <Skeleton lines={5} className="index-skeleton" />}
        <ul className="index-list">
          {categories.map((c) => (
            <li key={c.id}>
              <Link to={`/schemes?category=${c.id}`} className="index-row">
                <span className="index-icon"><Icon name={c.icon} size={24} /></span>
                <span className="index-main">
                  <strong>{pick(c.name, lang)}</strong>
                  <span>{pick(c.blurb, lang)}</span>
                </span>
                <span className="index-count">{c.scheme_count === 1 ? t('home.one') : t('home.many', { n: c.scheme_count })}</span>
                <Icon name="arrow-right" size={18} className="index-go" />
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

function How() {
  const { t } = useLang()
  return (
    <section className="section section-tint">
      <div className="wrap">
        <div className="section-head"><h2>{t('home.howTitle')}</h2></div>
        <ol className="steps">
          {t('home.steps').map((s, i) => (
            <li key={s.t}>
              <span className="step-num">{i + 1}</span>
              <h3>{s.t}</h3>
              <p>{s.d}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

function Trust() {
  const { t } = useLang()
  const icons = ['doc', 'shield', 'help']
  return (
    <section className="section section-dark">
      <div className="wrap">
        <div className="section-head"><h2>{t('home.trustTitle')}</h2></div>
        <div className="trust-grid">
          {t('home.trust').map((item, i) => (
            <div key={item.t} className="trust-item">
              <Icon name={icons[i]} size={26} />
              <h3>{item.t}</h3>
              <p>{item.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Cta() {
  const { t } = useLang()
  return (
    <section className="section">
      <div className="wrap cta">
        <div>
          <h2>{t('home.ctaTitle')}</h2>
          <p>{t('home.ctaBody')}</p>
        </div>
        <Link to="/eligibility" className="btn btn-primary btn-lg">
          {t('home.ctaBtn')} <Icon name="arrow-right" size={18} />
        </Link>
      </div>
    </section>
  )
}

export default function Home() {
  return (
    <>
      <Hero />
      <Browse />
      <How />
      <Trust />
      <Cta />
    </>
  )
}
