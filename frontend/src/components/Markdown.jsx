import { Fragment } from 'react'

// A deliberately small, safe markdown renderer for assistant answers.
// It builds React elements (never raw HTML), so model output cannot inject markup.
// Supports: paragraphs, **bold**, "- " bullets, "1. " lists and http(s) links.

const INLINE = /(\*\*[^*]+\*\*|https?:\/\/[^\s)]+)/g

function inline(text, keyBase) {
  return text.split(INLINE).map((part, i) => {
    if (!part) return null
    const key = `${keyBase}-${i}`
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={key}>{part.slice(2, -2)}</strong>
    if (/^https?:\/\//.test(part)) {
      const trailing = part.match(/[.,;:!?]+$/)?.[0] || ''
      const url = trailing ? part.slice(0, -trailing.length) : part
      return (
        <Fragment key={key}>
          <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>{trailing}
        </Fragment>
      )
    }
    return <Fragment key={key}>{part}</Fragment>
  })
}

export default function Markdown({ text }) {
  const blocks = []
  let list = null

  const flush = () => { if (list) { blocks.push(list); list = null } }

  text.replace(/\r/g, '').split('\n').forEach((raw, index) => {
    const line = raw.trim()
    if (!line) { flush(); return }

    const bullet = line.match(/^[-*•]\s+(.*)/)
    const numbered = line.match(/^\d+[.)]\s+(.*)/)
    if (bullet || numbered) {
      const type = bullet ? 'ul' : 'ol'
      if (!list || list.type !== type) { flush(); list = { type, items: [] } }
      list.items.push((bullet || numbered)[1])
      return
    }
    flush()
    blocks.push({ type: 'p', text: line, key: index })
  })
  flush()

  return (
    <div className="md">
      {blocks.map((b, i) => {
        if (b.type === 'p') return <p key={i}>{inline(b.text, i)}</p>
        const Tag = b.type
        return <Tag key={i}>{b.items.map((item, j) => <li key={j}>{inline(item, `${i}-${j}`)}</li>)}</Tag>
      })}
    </div>
  )
}
