declare module 'react-cytoscapejs' {
  import type { Core, ElementDefinition, LayoutOptions, StylesheetJsonBlock } from 'cytoscape'
  import type { Component, CSSProperties } from 'react'

  export interface CytoscapeComponentProps {
    elements: ElementDefinition[]
    style?: CSSProperties
    stylesheet?: StylesheetJsonBlock[]
    layout?: LayoutOptions
    cy?: (cy: Core) => void
    className?: string
    minZoom?: number
    maxZoom?: number
    zoom?: number
    pan?: { x: number; y: number }
    zoomingEnabled?: boolean
    userZoomingEnabled?: boolean
    panningEnabled?: boolean
    userPanningEnabled?: boolean
    boxSelectionEnabled?: boolean
    autoungrabify?: boolean
    autolock?: boolean
    autounselectify?: boolean
    wheelSensitivity?: number
    [key: string]: unknown
  }

  export default class CytoscapeComponent extends Component<CytoscapeComponentProps> {}
}
