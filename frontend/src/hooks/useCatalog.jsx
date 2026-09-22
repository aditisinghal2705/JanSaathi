import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

// Loads categories, schemes and health once and shares them with every page.
const CatalogContext = createContext(null)

export function CatalogProvider({ children }) {
  const [state, setState] = useState({ status: 'loading', categories: [], schemes: [], health: null })

  const load = useCallback(async () => {
    setState((s) => ({ ...s, status: 'loading' }))
    try {
      const [cats, schemes, health] = await Promise.all([
        api.categories(),
        api.schemes(),
        api.health().catch(() => null),
      ])
      setState({ status: 'ready', categories: cats.results, schemes: schemes.results, health })
    } catch {
      setState((s) => ({ ...s, status: 'error' }))
    }
  }, [])

  useEffect(() => { load() }, [load])

  const value = useMemo(() => {
    const byName = Object.fromEntries(state.categories.map((c) => [c.name.en, c]))
    return { ...state, reload: load, categoryOf: (scheme) => byName[scheme.category] || null }
  }, [state, load])

  return <CatalogContext.Provider value={value}>{children}</CatalogContext.Provider>
}

export function useCatalog() {
  const ctx = useContext(CatalogContext)
  if (!ctx) throw new Error('useCatalog must be used inside <CatalogProvider>')
  return ctx
}
