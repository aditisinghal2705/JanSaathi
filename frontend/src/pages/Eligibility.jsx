import { useRef, useState } from 'react'
import { api } from '../api/client'
import { ErrorState, PageHead } from '../components/Common'
import Icon from '../components/Icon'
import { useCategoryInfo } from '../components/SchemeCard'
import { useLang } from '../i18n'
import { Link } from '../router'

const SITUATIONS = [
  'punjab_resident_3y', 'student_post_matric', 'job_seeker', 'widow_or_destitute_woman',
  'construction_worker_family', 'daughter_marriage_planned', 'bpl_or_nfsa_household',
]
const GENDERS = ['female', 'male', 'other']
const CATEGORIES = ['sc', 'bc', 'general', 'other']

/** Turn a machine-readable reason from the API into a sentence in the current language. */
function useDescribe() {
  const { t } = useLang()
  const label = (type, value) => {
    if (type === 'category') return value.split('|').map((v) => t(`elig.cat.${v}`)).join(' / ')
    if (type === 'situation') return t(`elig.sit.${value}`)
    if (type === 'gender') return value.split('|').map((v) => t(`elig.${v}`)).join(' / ')
    return value
  }
  return (reason, kind) => {
    const key = `elig.r.${kind}_${reason.code}`
    let value = reason.values[0] ?? ''
    if (reason.code === 'any_of') {
      value = reason.values.map((d) => { const [type, ...rest] = d.split(':'); return label(type, rest.join(':')) }).join(', ')
    } else if (['category', 'situation', 'gender'].includes(reason.code)) {
      value = label(reason.code, reason.values.join('|'))
    }
    const text = t(key, { v: value })
    return text === key ? value : text
  }
}

function ReasonList({ title, items, kind, icon }) {
  const describe = useDescribe()
  if (!items.length) return null
  return (
    <div className={`reasons reasons-${kind}`}>
      <h4>{title}</h4>
      <ul>
        {items.map((r, i) => (
          <li key={`${r.code}-${i}`}><Icon name={icon} size={16} /> <span>{describe(r, kind)}</span></li>
        ))}
      </ul>
    </div>
  )
}

function MatchCard({ match }) {
  const { t } = useLang()
  const { label } = useCategoryInfo(match.scheme)
  return (
    <article className={`match match-${match.status}`}>
      <header>
        <span className="match-cat">{label}</span>
        <h4><Link to={`/schemes/${match.scheme.id}`}>{match.scheme.name}</Link></h4>
      </header>
      <ReasonList title={t('elig.met')} items={match.met} kind="met" icon="check" />
      <ReasonList title={t('elig.unmet')} items={match.unmet} kind="unmet" icon="close" />
      <ReasonList title={t('elig.verify')} items={match.verify} kind="verify" icon="info" />
      <Link to={`/schemes/${match.scheme.id}`} className="link-arrow">{t('schemes.open')} <Icon name="arrow-right" size={16} /></Link>
    </article>
  )
}

function Group({ status, matches, collapsed }) {
  const { t } = useLang()
  if (!matches.length) return null
  const head = (
    <>
      <h3><Icon name={status === 'likely' ? 'check-circle' : status === 'maybe' ? 'help' : 'x-circle'} size={22} /> {t(`elig.${status}`)} <span className="count">{matches.length}</span></h3>
      <p>{t(`elig.${status}D`)}</p>
    </>
  )
  const list = <div className="match-list">{matches.map((m) => <MatchCard key={m.scheme.id} match={m} />)}</div>
  if (collapsed) {
    return <details className={`group group-${status}`}><summary>{head}</summary>{list}</details>
  }
  return <section className={`group group-${status}`}><div className="group-head">{head}</div>{list}</section>
}

const EMPTY = { age: '', gender: '', category: '', situations: [] }

export default function Eligibility() {
  const { lang, t } = useLang()
  const [form, setForm] = useState(EMPTY)
  const [state, setState] = useState({ status: 'idle', results: [] })
  const resultsRef = useRef(null)

  const toggle = (value) => setForm((f) => ({
    ...f,
    situations: f.situations.includes(value) ? f.situations.filter((v) => v !== value) : [...f.situations, value],
  }))

  const submit = async (event) => {
    event.preventDefault()
    setState({ status: 'loading', results: [] })
    try {
      const age = form.age === '' ? null : Math.max(0, Math.min(120, parseInt(form.age, 10) || 0))
      const data = await api.eligibility({
        age, gender: form.gender || null, category: form.category || null,
        situations: form.situations, language: lang,
      })
      setState({ status: 'ready', results: data.results })
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60)
    } catch {
      setState({ status: 'error', results: [] })
    }
  }

  const reset = () => { setForm(EMPTY); setState({ status: 'idle', results: [] }) }
  const by = (status) => state.results.filter((m) => m.status === status)

  // A plain render helper (not a component) so React does not remount it on every change.
  const pills = ({ name, options, label }) => (
    <fieldset className="field">
      <legend>{label}</legend>
      <div className="pill-row">
        {options.map((o) => (
          <label key={o} className={`pill ${form[name] === o ? 'is-on' : ''}`}>
            <input type="radio" name={name} checked={form[name] === o} onChange={() => setForm({ ...form, [name]: o })} />
            {name === 'gender' ? t(`elig.${o}`) : t(`elig.cat.${o}`)}
          </label>
        ))}
        <label className={`pill pill-skip ${form[name] === '' ? 'is-on' : ''}`}>
          <input type="radio" name={name} checked={form[name] === ''} onChange={() => setForm({ ...form, [name]: '' })} />
          {t('elig.skip')}
        </label>
      </div>
    </fieldset>
  )

  return (
    <>
      <PageHead title={t('elig.title')} sub={t('elig.sub')} />
      <div className="wrap section-tight elig">
        <form className="form-card" onSubmit={submit}>
          <div className="field">
            <label htmlFor="age">{t('elig.age')}</label>
            <input id="age" type="number" inputMode="numeric" min="0" max="120" value={form.age}
              onChange={(e) => setForm({ ...form, age: e.target.value })} placeholder={t('elig.agePh')} />
          </div>
          {pills({ name: 'gender', options: GENDERS, label: t('elig.gender') })}
          {pills({ name: 'category', options: CATEGORIES, label: t('elig.category') })}

          <fieldset className="field">
            <legend>{t('elig.situations')}</legend>
            <div className="check-list">
              {SITUATIONS.map((s) => (
                <label key={s} className={`check ${form.situations.includes(s) ? 'is-on' : ''}`}>
                  <input type="checkbox" checked={form.situations.includes(s)} onChange={() => toggle(s)} />
                  <span className="check-box"><Icon name="check" size={14} /></span>
                  <span>{t(`elig.sit.${s}`)}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-lg" disabled={state.status === 'loading'}>
              {t('elig.check')} <Icon name="arrow-right" size={18} />
            </button>
            <button type="button" className="btn btn-quiet" onClick={reset}>{t('elig.reset')}</button>
          </div>
        </form>

        <div ref={resultsRef} className="results-area">
          {state.status === 'error' && <ErrorState message={t('elig.loadError')} />}
          {state.status === 'ready' && (
            <>
              <h2>{t('elig.resultsTitle')}</h2>
              <p className="callout"><Icon name="info" size={18} /> {t('elig.disclaimer')}</p>
              <Group status="likely" matches={by('likely')} />
              <Group status="maybe" matches={by('maybe')} />
              <Group status="unlikely" matches={by('unlikely')} collapsed />
            </>
          )}
        </div>
      </div>
    </>
  )
}
