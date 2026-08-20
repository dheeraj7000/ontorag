import { useRef, useState } from 'react'
import { uploadDocument, getIngestionStatus, type IngestionStatus } from '../api'

interface UploadPanelProps {
  onIngested?: () => void
}

export default function UploadPanel({ onIngested }: UploadPanelProps) {
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
      const status = await pollStatus(result.file_id)
      setJobs((prev) => [status, ...prev].slice(0, 8))
      onIngested?.()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(msg)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function pollStatus(fileId: string): Promise<IngestionStatus> {
    for (let i = 0; i < 15; i++) {
      await new Promise((r) => setTimeout(r, 2000))
      const status = await getIngestionStatus(fileId)
      if (status.status === 'completed' || status.status === 'error') {
        return status
      }
    }
    return await getIngestionStatus(fileId)
  }

  return (
    <section className="card">
      <div className="section-heading">
        <h2>Ingest a document</h2>
        <span className="card-header-meta">PDF · Markdown · HTML · TXT</span>
      </div>

      <div className="upload-layout">
        <div className="upload-zone" onClick={() => fileRef.current?.click()}>
          {uploading ? (
            <>
              <span className="spinner spinner-lg" />
              <p className="upload-title mt-3">Processing document...</p>
              <p className="upload-hint">Extracting entities &amp; relations</p>
            </>
          ) : (
            <>
              <div className="upload-icon">📄</div>
              <p className="upload-title">Click to upload</p>
              <p className="upload-hint">.pdf · .md · .html · .txt</p>
            </>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.md,.html,.txt"
            onChange={handleUpload}
          />
        </div>

        <div>
          <div className="upload-recent-title">Recent ingestions</div>
          {jobs.length === 0 ? (
            <p className="text-sm text-muted">Nothing ingested yet this session.</p>
          ) : (
            <ul className="upload-recent-list">
              {jobs.map((job) => (
                <li key={job.file_id} className="upload-recent-item">
                  <span className="filename">{job.filename}</span>
                  <span className="upload-recent-meta">
                    <span>{job.entities_inserted} ent · {job.relations_inserted} rel</span>
                    <span
                      className={`trust-badge trust-${job.status === 'completed' ? 'high' : job.status === 'error' ? 'low' : 'medium'}`}
                    >
                      {job.status}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {error && (
        <div className="alert alert-danger mt-4" style={{ marginBottom: 0 }}>
          <span className="alert-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}
    </section>
  )
}
