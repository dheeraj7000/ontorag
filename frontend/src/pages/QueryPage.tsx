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
        <h1>Query Knowledge Graph</h1>
        <p>Ask questions grounded in ontology-validated facts with trust scoring</p>
      </div>

      <div className="card">
        <form onSubmit={handleQuery}>
          <div className="input-group">
            <input
              type="text"
              placeholder="Ask a question about your ingested documents..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button className="btn" disabled={loading || !question.trim()}>
              {loading ? <span className="spinner" /> : 'Ask'}
            </button>
          </div>
          <div className="input-group" style={{ fontSize: '0.85rem' }}>
            <label style={{ color: 'var(--text-muted)' }}>
              Min Trust: {minTrust.toFixed(2)}
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={minTrust}
                onChange={(e) => setMinTrust(parseFloat(e.target.value))}
                style={{ marginLeft: '0.5rem', width: '150px' }}
              />
            </label>
          </div>
        </form>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)' }}>
          <p style={{ color: 'var(--danger)' }}>{error}</p>
        </div>
      )}

      {result && (
        <>
          <div className="card">
            <div className="card-header">
              <span>Answer</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                via {result.provider} | confidence: {result.confidence.toFixed(2)}
              </span>
            </div>
            <div className="answer-block">{result.answer}</div>
            {result.reasoning && (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
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
                      {fact.subject} <strong>—[{fact.relation}]→</strong> {fact.object}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.linked_entities.length > 0 && (
            <div className="card">
              <div className="card-header">Linked Entities</div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {result.linked_entities.map((e, i) => (
                  <span key={i} className="trust-badge trust-medium">{e}</span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
