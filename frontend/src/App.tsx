import { useCallback, useEffect, useState } from 'react'
import Hero from './components/Hero'
import UploadPanel from './components/UploadPanel'
import KnowledgeGraph from './components/KnowledgeGraph'
import TrustTools from './components/TrustTools'
import QueryPanel from './components/QueryPanel'
import { getGraphStats, type GraphStats } from './api'

function App() {
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(true)

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
    loadStats()
  }, [loadStats])

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
