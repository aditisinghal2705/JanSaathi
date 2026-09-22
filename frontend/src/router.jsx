import { useEffect, useState } from 'react'

// Tiny hash router (#/schemes/old-age-pension). Hash routing means the built site
// works on any static host or behind FastAPI with no server-side rewrite rules,
// and it needs no extra npm package.

function read() {
  const raw = window.location.hash.replace(/^#/, '') || '/'
  const [path, query = ''] = raw.split('?')
  return { path: path || '/', params: new URLSearchParams(query) }
}

export function useRoute() {
  const [route, setRoute] = useState(read)
  useEffect(() => {
    const onChange = () => setRoute(read())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}

export function navigate(to, { replace = false } = {}) {
  if (replace) {
    window.location.replace(`${window.location.pathname}${window.location.search}#${to}`)
  } else {
    window.location.hash = to
  }
}

export function Link({ to, children, ...rest }) {
  return <a href={`#${to}`} {...rest}>{children}</a>
}

export function withQuery(path, params) {
  const q = new URLSearchParams(params).toString()
  return q ? `${path}?${q}` : path
}
