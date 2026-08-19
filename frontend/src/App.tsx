import { Routes, Route, NavLink } from 'react-router-dom'
import QueryPage from './pages/QueryPage'
import IngestPage from './pages/IngestPage'
import GraphPage from './pages/GraphPage'
import TrustPage from './pages/TrustPage'

function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-logo">🧠 OntoRAG</div>
        <nav className="sidebar-nav">
          <NavLink to="/" end>Query</NavLink>
          <NavLink to="/ingest">Ingest</NavLink>
          <NavLink to="/graph">Graph</NavLink>
          <NavLink to="/trust">Trust</NavLink>
        </nav>
      </aside>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<QueryPage />} />
          <Route path="/ingest" element={<IngestPage />} />
          <Route path="/graph" element={<GraphPage />} />
          <Route path="/trust" element={<TrustPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
