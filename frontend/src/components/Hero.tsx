import type { GraphStats } from '../api'

interface HeroProps {
  stats: GraphStats | null
  loading: boolean
}

export default function Hero({ stats, loading }: HeroProps) {
  return (
    <section className="hero">
      <div className="hero-inner">
        <div className="hero-badge">
          <span className="dot" />
          Live knowledge graph · GNN-scored
        </div>
        <h1 className="hero-title">OntoRAG</h1>
        <p className="hero-tagline">
          Ontology-grounded RAG with GNN trust scoring — every answer is traced back to
          validated facts in a live knowledge graph, and every fact carries a learned
          trust score instead of a guess.
        </p>

        <div className="hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-value">
              {loading ? '—' : (stats?.total_nodes ?? 0).toLocaleString()}
            </div>
            <div className="hero-stat-label">Entities</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">
              {loading ? '—' : (stats?.total_edges ?? 0).toLocaleString()}
            </div>
            <div className="hero-stat-label">Relations</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">
              {loading ? '—' : (stats?.avg_trust_score ?? 0).toFixed(2)}
            </div>
            <div className="hero-stat-label">Avg Trust Score</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">
              {loading ? '—' : Object.keys(stats?.entity_types ?? {}).length}
            </div>
            <div className="hero-stat-label">Entity Types</div>
          </div>
        </div>
      </div>
    </section>
  )
}
