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
          <NavLink to="/" end><span className="nav-icon">🔍</span>Query</NavLink>
          <NavLink to="/ingest"><span className="nav-icon">📥</span>Ingest</NavLink>
          <NavLink to="/graph"><span className="nav-icon">🕸️</span>Graph</NavLink>
          <NavLink to="/trust"><span className="nav-icon">🛡️</span>Trust</NavLink>
        </nav>
        <div className="sidebar-footer">Ontology-grounded RAG</div>
      </aside>
      <main className="main-content">
        <div className="page">
          <Routes>
            <Route path="/" element={<QueryPage />} />
            <Route path="/ingest" element={<IngestPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/trust" element={<TrustPage />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

export default App
