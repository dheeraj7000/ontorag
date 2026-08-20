import { useEffect, useState, useCallback } from 'react'
import { getGraphStats, getSubgraph, getEntities, type GraphStats } from '../api'

export default function GraphPage() {
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [entities, setEntities] = useState<Array<{ name: string; entity_type: string; trust_score: number }>>([])
  const [selectedEntity, setSelectedEntity] = useState('')
  const [subgraph, setSubgraph] = useState<{ nodes: unknown[]; edges: unknown[] } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [statsData, entitiesData] = await Promise.all([
        getGraphStats(),
        getEntities({ limit: 50 }),
      ])
      setStats(statsData)
      setEntities(entitiesData.entities || [])
    } catch {
      // API might not be available
    } finally {
      setLoading(false)
    }
  }

  const handleEntityClick = useCallback(async (entityName: string) => {
    setSelectedEntity(entityName)
    try {
      const data = await getSubgraph(entityName, 2)
      setSubgraph(data)
    } catch {
      setSubgraph(null)
    }
  }, [])

  if (loading) {
    return (
      <div>
        <div className="page-header"><div><h1>Knowledge Graph</h1></div></div>
        <div className="card">
          <div className="loading-state">
            <span className="spinner" /> Loading graph data...
          </div>
        </div>
      </div>
    )
  }

  const hasData = !!stats

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Knowledge Graph Explorer</h1>
          <p>Browse entities, relations, and subgraphs</p>
        </div>
      </div>

      {!hasData && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">🕸️</div>
            <p>No graph data available. Ingest a document to get started.</p>
          </div>
        </div>
      )}

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_nodes}</div>
            <div className="stat-label">Total Entities</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.total_edges}</div>
            <div className="stat-label">Total Relations</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.avg_trust_score.toFixed(3)}</div>
            <div className="stat-label">Avg Trust Score</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{Object.keys(stats.entity_types).length}</div>
            <div className="stat-label">Entity Types</div>
          </div>
        </div>
      )}

      {stats && Object.keys(stats.entity_types).length > 0 && (
        <div className="card">
          <div className="card-header">Entity Type Distribution</div>
          <div className="chip-row">
            {Object.entries(stats.entity_types).map(([type, count]) => (
              <div key={type} className="chip">
                <strong>{type}</strong>: {count}
              </div>
            ))}
          </div>
        </div>
      )}

      {entities.length > 0 && (
        <div className="card">
          <div className="card-header">
            Entities
            <span className="card-header-meta">click a row to explore its subgraph</span>
          </div>
          <div className="table-scroll table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Trust</th>
                </tr>
              </thead>
              <tbody>
                {entities.map((entity) => (
                  <tr
                    key={entity.name}
                    onClick={() => handleEntityClick(entity.name)}
                    className={`is-clickable${selectedEntity === entity.name ? ' is-selected' : ''}`}
                  >
                    <td>{entity.name}</td>
                    <td><span className="badge">{entity.entity_type}</span></td>
                    <td>{entity.trust_score?.toFixed(2) || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {subgraph && (
        <div className="card">
          <div className="card-header">
            Subgraph: {selectedEntity}
            <span className="card-header-meta">
              {subgraph.nodes.length} nodes, {subgraph.edges.length} edges
            </span>
          </div>
          <div className="graph-container">
            <p>
              Cytoscape.js visualization renders here in production.
              <br />
              Nodes: {subgraph.nodes.length} | Edges: {subgraph.edges.length}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
