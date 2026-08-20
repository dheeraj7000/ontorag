import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Types
export interface QueryRequest {
  question: string
  min_trust?: number
  max_hops?: number
  top_k?: number
}

export interface QueryResponse {
  answer: string
  confidence: number
  provider: string
  used_facts: Array<{
    subject: string
    relation: string
    object: string
    trust_score: number
  }>
  provenance: Array<{
    fact_index: number
    source_document: string
    trust_score: number
  }>
  linked_entities: string[]
  reasoning: string
}

export interface GraphStats {
  total_nodes: number
  total_edges: number
  entity_types: Record<string, number>
  relation_types: Record<string, number>
  avg_trust_score: number
}

export interface IngestionResponse {
  status: string
  file_id: string
  filename: string
  size_bytes: number
  message: string
}

export interface IngestionStatus {
  file_id: string
  filename: string
  status: string
  total_chunks: number
  entities_extracted: number
  relations_extracted: number
  violations: number
  entities_inserted: number
  relations_inserted: number
  errors: string[]
}

export interface HallucinationResponse {
  hallucination_score: number
  claims: Array<{
    claim: string
    supported: boolean
    confidence: number
    evidence: string[]
  }>
  verdict: string
  total_claims: number
  supported_claims: number
  unsupported_claims: number
}

// API functions
export async function queryKG(request: QueryRequest): Promise<QueryResponse> {
  const { data } = await api.post('/query/', request)
  return data
}

export async function uploadDocument(file: File): Promise<IngestionResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/ingest/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getIngestionStatus(fileId: string): Promise<IngestionStatus> {
  const { data } = await api.get(`/ingest/status/${fileId}`)
  return data
}

export async function getGraphStats(): Promise<GraphStats> {
  const { data } = await api.get('/graph/stats')
  return data
}

export async function getEntities(params?: {
  entity_type?: string
  min_trust?: number
  limit?: number
}) {
  const { data } = await api.get('/graph/entities', { params })
  return data
}

export async function getSubgraph(entityName: string, hops = 2) {
  const { data } = await api.get(`/graph/subgraph/${encodeURIComponent(entityName)}`, {
    params: { hops },
  })
  return data
}

export interface GraphElements {
  nodes: Array<{ id: string; name: string; entity_type: string; trust_score: number }>
  edges: Array<{ source: string; target: string; type: string; trust_score: number | null }>
}

export async function getFullGraph(limit = 150): Promise<GraphElements> {
  const { data } = await api.get('/graph/full', { params: { limit } })
  return data
}

export async function checkHallucination(answer: string): Promise<HallucinationResponse> {
  const { data } = await api.post('/hallucination/check', { answer })
  return data
}

export async function computeTrustScores() {
  const { data } = await api.post('/trust/compute')
  return data
}

export async function getHealth() {
  const { data } = await api.get('/health', { baseURL: '' })
  return data
}
