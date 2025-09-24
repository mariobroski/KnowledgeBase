declare module 'react-force-graph-2d' {
  import { Component } from 'react';

  export interface NodeObject {
    id: string;
    name?: string;
    val?: number;
    color?: string;
    [key: string]: any;
  }

  export interface LinkObject {
    source: string | NodeObject;
    target: string | NodeObject;
    [key: string]: any;
  }

  export interface GraphData {
    nodes: NodeObject[];
    links: LinkObject[];
  }

  export interface ForceGraphProps {
    graphData: GraphData;
    nodeId?: string;
    nodeLabel?: string | ((node: NodeObject) => string);
    nodeVal?: string | ((node: NodeObject) => number);
    nodeRelSize?: number;
    nodeColor?: string | ((node: NodeObject) => string);
    nodeAutoColorBy?: string | ((node: NodeObject) => string);
    nodeCanvasObject?: (node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => void;
    nodeVisibility?: boolean | ((node: NodeObject) => boolean);
    linkSource?: string;
    linkTarget?: string;
    linkLabel?: string | ((link: LinkObject) => string);
    linkVisibility?: boolean | ((link: LinkObject) => boolean);
    linkColor?: string | ((link: LinkObject) => string);
    linkAutoColorBy?: string | ((link: LinkObject) => string);
    linkWidth?: number | ((link: LinkObject) => number);
    linkCurvature?: number | ((link: LinkObject) => number);
    linkDirectionalArrowLength?: number | ((link: LinkObject) => number);
    linkDirectionalArrowColor?: string | ((link: LinkObject) => string);
    linkDirectionalArrowRelPos?: number | ((link: LinkObject) => number);
    linkDirectionalParticles?: number | ((link: LinkObject) => number);
    linkDirectionalParticleSpeed?: number | ((link: LinkObject) => number);
    linkDirectionalParticleColor?: string | ((link: LinkObject) => string);
    linkDirectionalParticleWidth?: number | ((link: LinkObject) => number);
    d3AlphaDecay?: number;
    d3VelocityDecay?: number;
    warmupTicks?: number;
    cooldownTicks?: number;
    cooldownTime?: number;
    onNodeClick?: (node: NodeObject, event: MouseEvent) => void;
    onNodeRightClick?: (node: NodeObject, event: MouseEvent) => void;
    onNodeHover?: (node: NodeObject | null, previousNode: NodeObject | null) => void;
    onNodeDrag?: (node: NodeObject, translate: { x: number, y: number }) => void;
    onNodeDragEnd?: (node: NodeObject, translate: { x: number, y: number }) => void;
    onLinkClick?: (link: LinkObject, event: MouseEvent) => void;
    onLinkRightClick?: (link: LinkObject, event: MouseEvent) => void;
    onLinkHover?: (link: LinkObject | null, previousLink: LinkObject | null) => void;
    onBackgroundClick?: (event: MouseEvent) => void;
    onBackgroundRightClick?: (event: MouseEvent) => void;
    onEngineStop?: () => void;
    width?: number;
    height?: number;
    backgroundColor?: string;
    showNavInfo?: boolean;
    [key: string]: any;
  }

  export default class ForceGraph2D extends Component<ForceGraphProps> {
    // Methods
    zoom(factor: number, duration?: number): ForceGraph2D;
    centerAt(x?: number, y?: number, duration?: number): ForceGraph2D;
    d3Force(forceName: string, forceFn?: any): any;
    d3ReheatSimulation(): ForceGraph2D;
    refresh(): ForceGraph2D;
  }
}