import { useState } from 'react'
import { computeTrustScores, checkHallucination, type HallucinationResponse } from '../api'

export default function TrustPage() {
  const [computing, setComputing] = useState(false)
  const [trustResult, setTrustResult] = useState<Record<string, unknown> | null>(null)

  const [answer, setAnswer] = useState('')
  const [checking, setChecking] = useState(false)
  const [hallucinationResult, setHallucinationResult] = useState<HallucinationResponse | null>(null)

  async function handleComputeTrust() {
    setComputing(true)
    try {
      const result = await computeTrustScores()
      setTrustResult(result)
    } catch {
      setTrustResult({ status: 'error', message: 'Failed to compute trust scores' })
    } finally {
      setComputing(false)
    }
  }

  async function handleCheckHallucination(e: React.FormEvent) {
    e.preventDefault()
    if (!answer.trim()) return

    setChecking(true)
    try {
      const result = await checkHallucination(answer)
      setHallucinationResult(result)
    } catch {
      setHallucinationResult(null)
    } finally {
      setChecking(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Trust & Hallucination</h1>
        <p>GNN trust scoring and answer verification</p>
      </div>

      {/* Trust Scoring */}
      <div className="card">
        <div className="card-header">GNN Trust Scoring</div>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem', fontSize: '0.9rem' }}>
          Train the Graph Attention Network on the current knowledge graph to compute
          trust scores for all entities based on extraction confidence, source count,
          and neighborhood agreement.
        </p>
        <button className="btn" onClick={handleComputeTrust} disabled={computing}>
          {computing ? <><span className="spinner" /> Computing...</> : 'Compute Trust Scores'}
        </button>

        {trustResult && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg)', borderRadius: '0.5rem' }}>
            <pre style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {JSON.stringify(trustResult, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Hallucination Detection */}
      <div className="card">
        <div className="card-header">Hallucination Detection</div>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem', fontSize: '0.9rem' }}>
          Paste an LLM-generated answer to check if its claims are supported by the knowledge graph.
        </p>
        <form onSubmit={handleCheckHallucination}>
          <textarea
            placeholder="Paste an answer to verify against the knowledge graph..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
          <button className="btn" style={{ marginTop: '0.75rem' }} disabled={checking || !answer.trim()}>
            {checking ? <><span className="spinner" /> Checking...</> : 'Check for Hallucinations'}
          </button>
        </form>

        {hallucinationResult && (
          <div style={{ marginTop: '1.5rem' }}>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value" style={{
                  color: hallucinationResult.hallucination_score <= 0.3
                    ? 'var(--trust-high)'
                    : hallucinationResult.hallucination_score <= 0.6
                    ? 'var(--trust-medium)'
                    : 'var(--trust-low)'
                }}>
                  {(hallucinationResult.hallucination_score * 100).toFixed(0)}%
                </div>
                <div className="stat-label">Hallucination Score</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{hallucinationResult.supported_claims}</div>
                <div className="stat-label">Supported Claims</div>
              </div>
              <div className="stat-card">
                <div className="stat-value" style={{ color: 'var(--danger)' }}>
                  {hallucinationResult.unsupported_claims}
                </div>
                <div className="stat-label">Unsupported Claims</div>
              </div>
            </div>

            <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>{hallucinationResult.verdict}</p>

            {hallucinationResult.claims.length > 0 && (
              <ul className="facts-list">
                {hallucinationResult.claims.map((claim, i) => (
                  <li key={i}>
                    <span className={`trust-badge trust-${claim.supported ? 'high' : 'low'}`}>
                      {claim.supported ? '✓' : '✗'}
                    </span>
                    <span>{claim.claim}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
