import { useRef, useState } from 'react'
import { uploadDocument, getIngestionStatus, type IngestionStatus } from '../api'

export default function IngestPage() {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [jobs, setJobs] = useState<IngestionStatus[]>([])
  const [error, setError] = useState('')

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError('')
    try {
      const result = await uploadDocument(file)

      // Poll for status
      const status = await pollStatus(result.file_id)
      setJobs((prev) => [status, ...prev])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(msg)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function pollStatus(fileId: string): Promise<IngestionStatus> {
    // Simple poll: check every 2 seconds, up to 30 seconds
    for (let i = 0; i < 15; i++) {
      await new Promise((r) => setTimeout(r, 2000))
      const status = await getIngestionStatus(fileId)
      if (status.status === 'completed' || status.status === 'error') {
        return status
      }
    }
    // Return whatever we have
    return await getIngestionStatus(fileId)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Ingest Documents</h1>
        <p>Upload documents to build the knowledge graph (PDF, Markdown, HTML, TXT)</p>
      </div>

      <div className="card">
        <div
          className="upload-zone"
          onClick={() => fileRef.current?.click()}
        >
          {uploading ? (
            <>
              <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
              <p style={{ marginTop: '1rem' }}>Processing document...</p>
            </>
          ) : (
            <>
              <p style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
                📄 Click to upload a document
              </p>
              <p style={{ color: 'var(--text-muted)' }}>
                Supports: .pdf, .md, .html, .txt
              </p>
            </>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.md,.html,.txt"
            onChange={handleUpload}
          />
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)' }}>
          <p style={{ color: 'var(--danger)' }}>{error}</p>
        </div>
      )}

      {jobs.length > 0 && (
        <div className="card">
          <div className="card-header">Ingestion History</div>
          <table style={{ width: '100%', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>File</th>
                <th>Status</th>
                <th>Chunks</th>
                <th>Entities</th>
                <th>Relations</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.file_id} style={{ borderTop: '1px solid var(--border)' }}>
                  <td style={{ padding: '0.5rem' }}>{job.filename}</td>
                  <td>
                    <span className={`trust-badge trust-${job.status === 'completed' ? 'high' : job.status === 'error' ? 'low' : 'medium'}`}>
                      {job.status}
                    </span>
                  </td>
                  <td>{job.total_chunks}</td>
                  <td>{job.entities_inserted}</td>
                  <td>{job.relations_inserted}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
