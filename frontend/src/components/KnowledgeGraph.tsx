import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import type { Core, Css, ElementDefinition, EventObject, LayoutOptions, StylesheetJsonBlock } from 'cytoscape'
import { getFullGraph, getSubgraph, type GraphElements } from '../api'

type GraphNode = GraphElements['nodes'][number]
type GraphEdge = GraphElements['edges'][number]

interface NeighborFact {
  otherName: string
  relation: string
  direction: 'out' | 'in'
  trust_score: number | null
}

const LOW_COLOR = { r: 239, g: 68, b: 68 } // trust-low
const MID_COLOR = { r: 245, g: 158, b: 11 } // trust-medium
const HIGH_COLOR = { r: 34, g: 197, b: 94 } // trust-high

function lerp(a: number, b: number, t: number) {
  return Math.round(a + (b - a) * t)
}

function trustToColor(score: number | null | undefined): string {
  const s = Math.max(0, Math.min(1, score ?? 0))
  const [from, to, t] = s < 0.5 ? [LOW_COLOR, MID_COLOR, s / 0.5] : [MID_COLOR, HIGH_COLOR, (s - 0.5) / 0.5]
  return `rgb(${lerp(from.r, to.r, t)}, ${lerp(from.g, to.g, t)}, ${lerp(from.b, to.b, t)})`
}

function trustToSize(score: number | null | undefined): number {
  const s = Math.max(0, Math.min(1, score ?? 0))
  return 22 + s * 30
}

const SHAPES = ['ellipse', 'round-rectangle', 'round-diamond', 'round-triangle', 'round-hexagon', 'round-tag']

function hashString(str: string): number {
  let h = 0
  for (let i = 0; i < str.length; i++) {
    h = (h * 31 + str.charCodeAt(i)) | 0
  }
  return Math.abs(h)
}

function entityShape(entityType: string | undefined): string {
  if (!entityType) return 'ellipse'
  return SHAPES[hashString(entityType) % SHAPES.length]
}

function toElements(nodes: GraphNode[], edges: GraphEdge[]): ElementDefinition[] {
  const nodeEls: ElementDefinition[] = nodes.map((n) => ({
    data: {
      id: n.id,
      label: n.name,
      entity_type: n.entity_type,
      trust_score: n.trust_score,
      color: trustToColor(n.trust_score),
      size: trustToSize(n.trust_score),
      shape: entityShape(n.entity_type),
    },
  }))

  const seenIds = new Map<string, number>()
  const edgeEls: ElementDefinition[] = edges.map((e) => {
    const baseId = `${e.source}-${e.target}-${e.type}`
    const count = seenIds.get(baseId) ?? 0
    seenIds.set(baseId, count + 1)
    const id = count === 0 ? baseId : `${baseId}-${count}`
    return {
      data: {
        id,
        source: e.source,
        target: e.target,
        label: e.type,
        trust_score: e.trust_score,
        width: 1 + Math.max(0, Math.min(1, e.trust_score ?? 0.4)) * 3,
      },
    }
  })

  return [...nodeEls, ...edgeEls]
}

const stylesheet: StylesheetJsonBlock[] = [
  {
    selector: 'node',
    style: {
      'background-color': 'data(color)',
      width: 'data(size)',
      height: 'data(size)',
      shape: 'data(shape)' as unknown as Css.NodeShape,
      label: 'data(label)',
      color: '#e6ebf3',
      'font-size': 9,
      'text-valign': 'bottom',
      'text-margin-y': 6,
      'text-wrap': 'ellipsis',
      'text-max-width': '80px',
      'border-width': 2,
      'border-color': 'rgba(11, 18, 32, 0.7)',
      'text-outline-width': 2,
      'text-outline-color': '#0b1220',
    },
  },
  {
    selector: 'node.center-node',
    style: {
      'border-width': 5,
      'border-color': '#67e8f9',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 5,
      'border-color': '#a78bfa',
    },
  },
  {
    selector: 'edge',
    style: {
      width: 'data(width)',
      'line-color': 'rgba(148, 163, 184, 0.35)',
      'target-arrow-color': 'rgba(148, 163, 184, 0.55)',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'arrow-scale': 0.7,
      opacity: 0.9,
    },
  },
  {
    selector: 'edge:selected',
    style: {
      'line-color': '#a78bfa',
      'target-arrow-color': '#a78bfa',
      width: 3,
    },
  },
]

const cosePreset = {
  name: 'cose',
  animate: false,
  fit: true,
  padding: 40,
  nodeOverlap: 12,
  idealEdgeLength: 90,
  nodeRepulsion: 6000,
  gravity: 45,
} as unknown as LayoutOptions

export default function KnowledgeGraph() {
  const [fullGraph, setFullGraph] = useState<GraphElements | null>(null)
  const [elements, setElements] = useState<ElementDefinition[]>([])
  const [loading, setLoading] = useState(true)
  const [subLoading, setSubLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [neighborFacts, setNeighborFacts] = useState<NeighborFact[]>([])
  const [isSubgraphView, setIsSubgraphView] = useState(false)
  const cyRef = useRef<Core | null>(null)

  const loadFullGraph = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getFullGraph(150)
      setFullGraph(data)
      setElements(toElements(data.nodes, data.edges))
      setIsSubgraphView(false)
    } catch {
      setError('Could not load graph data. Ingest a document to get started.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadFullGraph()
  }, [loadFullGraph])

  const handleNodeTap = useCallback(async (evt: EventObject) => {
    const node = evt.target
    const data = node.data() as { id: string; label: string; entity_type: string; trust_score: number }
    const nodeInfo: GraphNode = {
      id: data.id,
      name: data.label,
      entity_type: data.entity_type,
      trust_score: data.trust_score,
    }
    setSelectedNode(nodeInfo)
    setSubLoading(true)
    try {
      const sub = (await getSubgraph(nodeInfo.name, 2)) as GraphElements & { center?: string }
      setElements(toElements(sub.nodes, sub.edges))
      setIsSubgraphView(true)

      const facts: NeighborFact[] = sub.edges
        .filter((e) => e.source === nodeInfo.id || e.target === nodeInfo.id)
        .map((e) => {
          const outgoing = e.source === nodeInfo.id
          const otherId = outgoing ? e.target : e.source
          const other = sub.nodes.find((n) => n.id === otherId)
          return {
            otherName: other?.name ?? otherId,
            relation: e.type,
            direction: outgoing ? ('out' as const) : ('in' as const),
            trust_score: e.trust_score,
          }
        })
        .slice(0, 20)
      setNeighborFacts(facts)
    } catch {
      setNeighborFacts([])
    } finally {
      setSubLoading(false)
    }
  }, [])

  const handleCyInit = useCallback((cy: Core) => {
    cyRef.current = cy
    cy.off('tap', 'node')
    cy.on('tap', 'node', (evt) => {
      handleNodeTap(evt)
    })
  }, [handleNodeTap])

  // Re-apply the center-node highlight class whenever selection/elements change.
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.nodes().removeClass('center-node')
    if (selectedNode) {
      cy.getElementById(selectedNode.id).addClass('center-node')
    }
  }, [elements, selectedNode])

  const handleReset = useCallback(() => {
    if (!fullGraph) return
    setElements(toElements(fullGraph.nodes, fullGraph.edges))
    setIsSubgraphView(false)
    setSelectedNode(null)
    setNeighborFacts([])
  }, [fullGraph])

  const layout = useMemo(() => cosePreset, [])

  const hasData = elements.some((el) => el.data && 'label' in el.data)

  return (
    <section className="card graph-panel">
      <div className="graph-panel-header">
        <div className="section-heading" style={{ margin: 0 }}>
          <h2>Knowledge graph</h2>
        </div>
        <div className="graph-legend">
          <span className="graph-legend-item">
            <span className="graph-legend-swatch" style={{ background: trustToColor(0.1) }} />
            Low trust
          </span>
          <span className="graph-legend-item">
            <span className="graph-legend-swatch" style={{ background: trustToColor(0.5) }} />
            Medium
          </span>
          <span className="graph-legend-item">
            <span className="graph-legend-swatch" style={{ background: trustToColor(0.95) }} />
            High trust
          </span>
          <span className="graph-legend-item">size ∝ trust · shape ∝ entity type</span>
        </div>
      </div>

      <div className="graph-body">
        {isSubgraphView && (
          <div className="graph-toolbar">
            <button className="btn btn-secondary" onClick={handleReset}>
              ← Full graph
            </button>
          </div>
        )}

        {loading && (
          <div className="graph-loading">
            <span className="spinner spinner-lg" />
            <p>Loading knowledge graph…</p>
          </div>
        )}

        {!loading && error && (
          <div className="graph-empty">
            <div className="empty-icon">🕸️</div>
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && !hasData && (
          <div className="graph-empty">
            <div className="empty-icon">🕸️</div>
            <p>No graph data yet. Ingest a document above to populate the graph.</p>
          </div>
        )}

        {!loading && !error && hasData && (
          <CytoscapeComponent
            elements={elements}
            stylesheet={stylesheet}
            layout={layout}
            cy={handleCyInit}
            className="graph-canvas"
            wheelSensitivity={0.25}
            minZoom={0.15}
            maxZoom={3}
          />
        )}

        {selectedNode && (
          <div className="graph-detail">
            <div className="graph-detail-title">
              <span>
                {selectedNode.name}{' '}
                <span className="badge">{selectedNode.entity_type}</span>
              </span>
              <button
                className="graph-detail-close"
                onClick={() => {
                  setSelectedNode(null)
                  setNeighborFacts([])
                }}
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-muted">
              Trust score: <strong style={{ color: trustToColor(selectedNode.trust_score) }}>
                {(selectedNode.trust_score ?? 0).toFixed(2)}
              </strong>
            </p>
            {subLoading ? (
              <p className="text-sm text-muted mt-2">Loading neighborhood…</p>
            ) : neighborFacts.length > 0 ? (
              <ul className="graph-detail-facts mt-2">
                {neighborFacts.map((f, i) => (
                  <li key={i}>
                    <span className="fact-relation">
                      {f.direction === 'out' ? `—[${f.relation}]→` : `←[${f.relation}]—`}
                    </span>
                    <span>{f.otherName}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted mt-2">No connected facts found.</p>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
