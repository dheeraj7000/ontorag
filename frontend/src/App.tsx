import { useCallback, useEffect, useRef, useState } from 'react'
import Hero from './components/Hero'
import UploadPanel from './components/UploadPanel'
import KnowledgeGraph from './components/KnowledgeGraph'
import TrustTools from './components/TrustTools'
import QueryPanel from './components/QueryPanel'
import { getGraphStats, resetDemo, type GraphStats } from './api'

function App() {
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(true)
  const [ready, setReady] = useState(false)
  const resetOnce = useRef(false)

  const loadStats = useCallback(async () => {
    try {
      const data = await getGraphStats()
      setStats(data)
    } catch {
      // Backend may not be reachable yet — hero just shows placeholders.
    } finally {
      setStatsLoading(false)
    }
  }, [])

  useEffect(() => {
    // Demo mode: no auth/per-user isolation yet, so every visitor shares
    // one knowledge graph. Reset it before any child component fetches
    // anything, so nobody sees a previous visitor's data — not even
    // briefly while the page loads.
    if (resetOnce.current) return
    resetOnce.current = true
    resetDemo()
      .catch(() => {
        // If the reset call fails (e.g. backend briefly down), still show
        // the page rather than getting stuck — worst case, stale data.
      })
      .finally(() => {
        setReady(true)
        loadStats()
      })
  }, [loadStats])

  if (!ready) {
    return (
      <div className="shell boot-shell">
        <span className="spinner spinner-lg" />
        <p className="text-muted mt-3">Preparing a fresh demo…</p>
      </div>
    )
  }

  return (
    <div className="shell">
      <div className="layout-grid">
        <div className="main-col">
          <Hero stats={stats} loading={statsLoading} />
          <UploadPanel onIngested={loadStats} />
          <KnowledgeGraph />
          <TrustTools />
        </div>
        <div className="side-col">
          <QueryPanel />
        </div>
      </div>
    </div>
  )
}

export default App
