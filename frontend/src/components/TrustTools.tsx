import { useState } from 'react'
import { computeTrustScores, checkHallucination, type HallucinationResponse } from '../api'

export default function TrustTools() {
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

  const scoreClass = (score: number) =>
    score <= 0.3 ? 'stat-good' : score <= 0.6 ? 'stat-warn' : 'stat-bad'

  return (
    <section className="card">
      <div className="section-heading">
        <h2>Trust &amp; hallucination tools</h2>
        <span className="card-header-meta">GNN scoring · answer verification</span>
      </div>

      <div className="upload-layout">
        <div>
          <p className="card-subtitle">
            Train the Graph Attention Network on the current graph to recompute trust
            scores from extraction confidence, source count, and neighborhood agreement.
          </p>
          <button className="btn" onClick={handleComputeTrust} disabled={computing}>
            {computing ? <><span className="spinner" /> Computing...</> : 'Compute Trust Scores'}
          </button>
          {trustResult && (
            <div className="code-block">
              <pre>{JSON.stringify(trustResult, null, 2)}</pre>
            </div>
          )}
        </div>

        <div>
          <p className="card-subtitle">
            Paste an LLM-generated answer to check its claims against the knowledge graph.
          </p>
          <form onSubmit={handleCheckHallucination}>
            <textarea
              className="textarea"
              placeholder="Paste an answer to verify..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
            />
            <button className="btn mt-3" disabled={checking || !answer.trim()}>
              {checking ? <><span className="spinner" /> Checking...</> : 'Check for Hallucinations'}
            </button>
          </form>

          {hallucinationResult && (
            <div className="mt-4">
              <div className="stats-grid" style={{ marginBottom: 'var(--space-4)' }}>
                <div className="stat-card">
                  <div className={`stat-value ${scoreClass(hallucinationResult.hallucination_score)}`}>
                    {(hallucinationResult.hallucination_score * 100).toFixed(0)}%
                  </div>
                  <div className="stat-label">Hallucination</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value stat-good">{hallucinationResult.supported_claims}</div>
                  <div className="stat-label">Supported</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value stat-bad">{hallucinationResult.unsupported_claims}</div>
                  <div className="stat-label">Unsupported</div>
                </div>
              </div>

              <p className="text-sm">{hallucinationResult.verdict}</p>

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
    </section>
  )
}
