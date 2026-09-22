import { useEffect } from 'react'
import Footer from './components/Footer'
import Header from './components/Header'
import { PhulkariDefs } from './components/Phulkari'
import { CatalogProvider } from './hooks/useCatalog'
import { ChatProvider } from './hooks/useChat'
import { LangProvider, useLang } from './i18n'
import About from './pages/About'
import Assistant from './pages/Assistant'
import Eligibility from './pages/Eligibility'
import Home from './pages/Home'
import NotFound from './pages/NotFound'
import SchemeDetail from './pages/SchemeDetail'
import Schemes from './pages/Schemes'
import { useRoute } from './router'

function Routes({ path, params }) {
  if (path === '/') return <Home />
  if (path === '/schemes') return <Schemes params={params} />
  if (path.startsWith('/schemes/')) return <SchemeDetail id={decodeURIComponent(path.slice('/schemes/'.length))} />
  if (path === '/eligibility') return <Eligibility />
  if (path === '/assistant') return <Assistant params={params} />
  if (path === '/about') return <About />
  return <NotFound />
}

function Shell() {
  const { t } = useLang()
  const { path, params } = useRoute()
  const isChat = path === '/assistant'

  // start each page at the top (the chat page scrolls internally)
  useEffect(() => { window.scrollTo(0, 0) }, [path])

  return (
    <div className={`app ${isChat ? 'app-chat' : ''}`}>
      <a href="#main" className="skip-link" onClick={(e) => { e.preventDefault(); document.getElementById('main')?.focus() }}>{t('skip')}</a>
      <PhulkariDefs />
      <Header path={path} />
      <main id="main" tabIndex={-1}>
        <Routes path={path} params={params} />
      </main>
      {!isChat && <Footer />}
    </div>
  )
}

export default function App() {
  return (
    <LangProvider>
      <CatalogProvider>
        <ChatProvider>
          <Shell />
        </ChatProvider>
      </CatalogProvider>
    </LangProvider>
  )
}
