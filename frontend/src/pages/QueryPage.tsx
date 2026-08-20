import { useState } from 'react'
import { queryKG, type QueryResponse } from '../api'

function TrustBadge({ score }: { score: number }) {
  const level = score >= 0.75 ? 'high' : score >= 0.5 ? 'medium' : 'low'
  return <span className={`trust-badge trust-${level}`}>{score.toFixed(2)}</span>
}

export default function QueryPage() {
  const [question, setQuestion] = useState('')
  const [minTrust, setMinTrust] = useState(0.5)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [error, setError] = useState('')

  async function handleQuery(e: React.FormEvent) {
    e.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setError('')
    try {
      const response = await queryKG({ question, min_trust: minTrust })
      setResult(response)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Query failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Query Knowledge Graph</h1>
          <p>Ask questions grounded in ontology-validated facts with trust scoring</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleQuery}>
          <div className="input-group">
            <input
              type="text"
              className="input"
              placeholder="Ask a question about your ingested documents..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button className="btn" disabled={loading || !question.trim()}>
              {loading ? <span className="spinner" /> : 'Ask'}
            </button>
          </div>
          <div className="range-row">
            <label className="field-label">
              Min Trust: {minTrust.toFixed(2)}
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={minTrust}
                onChange={(e) => setMinTrust(parseFloat(e.target.value))}
              />
            </label>
          </div>
        </form>
      </div>

      {error && (
        <div className="alert alert-danger">
          <span className="alert-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {!result && !error && !loading && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <p>Ask a question above to get a grounded answer from the knowledge graph.</p>
          </div>
        </div>
      )}

      {result && (
        <>
          <div className="card">
            <div className="card-header">
              <span>Answer</span>
              <span className="card-header-meta">
                via {result.provider} · confidence {result.confidence.toFixed(2)}
              </span>
            </div>
            <div className="answer-block">{result.answer}</div>
            {result.reasoning && (
              <p className="reasoning-note">
                <strong>Reasoning:</strong> {result.reasoning}
              </p>
            )}
          </div>

          {result.used_facts.length > 0 && (
            <div className="card">
              <div className="card-header">Supporting Facts</div>
              <ul className="facts-list">
                {result.used_facts.map((fact, i) => (
                  <li key={i}>
                    <TrustBadge score={fact.trust_score} />
                    <span>
                      {fact.subject} <span className="fact-relation">—[{fact.relation}]→</span> {fact.object}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.linked_entities.length > 0 && (
            <div className="card">
              <div className="card-header">Linked Entities</div>
              <div className="chip-row">
                {result.linked_entities.map((e, i) => (
                  <span key={i} className="chip">{e}</span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
