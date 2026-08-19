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
        <div className="page-header"><h1>Knowledge Graph</h1></div>
        <div className="card"><span className="spinner" /> Loading graph data...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1>Knowledge Graph Explorer</h1>
        <p>Browse entities, relations, and subgraphs</p>
      </div>

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
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {Object.entries(stats.entity_types).map(([type, count]) => (
              <div key={type} style={{ padding: '0.5rem 1rem', background: 'var(--bg)', borderRadius: '0.5rem' }}>
                <strong>{type}</strong>: {count}
              </div>
            ))}
          </div>
        </div>
      )}

      {entities.length > 0 && (
        <div className="card">
          <div className="card-header">Entities (click to explore subgraph)</div>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table style={{ width: '100%', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
                  <th style={{ padding: '0.5rem' }}>Name</th>
                  <th>Type</th>
                  <th>Trust</th>
                </tr>
              </thead>
              <tbody>
                {entities.map((entity) => (
                  <tr
                    key={entity.name}
                    onClick={() => handleEntityClick(entity.name)}
                    style={{
                      cursor: 'pointer',
                      borderTop: '1px solid var(--border)',
                      background: selectedEntity === entity.name ? 'rgba(99, 102, 241, 0.1)' : undefined,
                    }}
                  >
                    <td style={{ padding: '0.5rem' }}>{entity.name}</td>
                    <td><span className="trust-badge trust-medium">{entity.entity_type}</span></td>
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
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {subgraph.nodes.length} nodes, {subgraph.edges.length} edges
            </span>
          </div>
          <div className="graph-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <p style={{ color: 'var(--text-muted)' }}>
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
