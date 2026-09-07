import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Network, type Options } from 'vis-network';
import { DataSet } from 'vis-data';
import { Maximize2, ZoomIn, ZoomOut, RefreshCw, SlidersHorizontal } from 'lucide-react';
import type { Clause, ClauseRisk, GraphEdge, InternalContradiction } from '../../types/contract';
import { getRiskLevel } from '../../utils/formatters';

interface KnowledgeGraphProps {
  clauses: Clause[];
  edges: GraphEdge[];
  risks: ClauseRisk[];
  contradictions: InternalContradiction[];
  highThreshold: number;
  mediumThreshold: number;
  onSelectClause?: (clauseIndex: number) => void;
}

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  clauses,
  edges,
  risks,
  contradictions,
  highThreshold,
  mediumThreshold,
  onSelectClause,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [selectedNodeInfo, setSelectedNodeInfo] = useState<{ id: number; label: string; text: string; risk: string } | null>(null);
  const [edgeThreshold, setEdgeThreshold] = useState<number>(0.82); // Default cleaner, sparser threshold

  const contradictionPairs = useMemo(() => {
    const set = new Set<string>();
    for (const c of contradictions) {
      set.add(`${c.clause_a_index}-${c.clause_b_index}`);
      set.add(`${c.clause_b_index}-${c.clause_a_index}`);
    }
    return set;
  }, [contradictions]);

  // Filter edges based on similarity threshold while always retaining contradiction links
  const visibleEdges = useMemo(() => {
    return edges.filter((e) => {
      const isContradiction = contradictionPairs.has(`${e.source_index}-${e.target_index}`);
      return isContradiction || e.similarity >= edgeThreshold;
    });
  }, [edges, contradictionPairs, edgeThreshold]);

  useEffect(() => {
    if (!containerRef.current || !clauses || clauses.length === 0) return;

    const riskMap = new Map<number, string>();
    for (const r of risks) {
      riskMap.set(r.clause_index, getRiskLevel(r.top_score, highThreshold, mediumThreshold));
    }

    // Nodes dataset
    const nodesArray = clauses.map((clause) => {
      const level = riskMap.get(clause.index) || 'LOW';
      let color = '#10B981'; // green
      let size = 16;

      if (level === 'HIGH') {
        color = '#EF4444';
        size = 22;
      } else if (level === 'MEDIUM') {
        color = '#F59E0B';
        size = 18;
      }

      const snippet = clause.text.length > 200 ? `${clause.text.slice(0, 200)}...` : clause.text;

      return {
        id: clause.index,
        label: `Clause ${clause.index}`,
        title: `<b>Clause ${clause.index}</b> (${level} Risk)<br>${snippet}`,
        color: {
          background: color,
          border: color,
          highlight: {
            background: color,
            border: '#0F172A',
          },
        },
        font: {
          color: '#0F172A',
          size: 12,
          face: 'Inter, sans-serif',
          strokeWidth: 2,
          strokeColor: '#FFFFFF',
        },
        size: size,
        originalColor: color,
      };
    });

    // Edges dataset
    const edgesArray = visibleEdges.map((e, idx) => {
      const isContradiction = contradictionPairs.has(`${e.source_index}-${e.target_index}`);

      return {
        id: `e_${idx}_${e.source_index}_${e.target_index}`,
        from: e.source_index,
        to: e.target_index,
        color: isContradiction ? { color: '#EF4444', highlight: '#DC2626' } : { color: '#CBD5E1', highlight: '#6366F1' },
        width: isContradiction ? 2.5 : Math.max(1, (e.similarity - 0.7) * 4),
        dashes: isContradiction,
        title: isContradiction
          ? `<b>CONTRADICTION DETECTED</b>`
          : `Similarity: ${(e.similarity * 100).toFixed(1)}%`,
      };
    });

    const nodes = new DataSet<any>(nodesArray);
    const edgesData = new DataSet<any>(edgesArray);

    const options: Options = {
      nodes: {
        shape: 'dot',
      },
      edges: {
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.2,
        },
      },
      physics: {
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -60,
          centralGravity: 0.01,
          springLength: 110,
          springConstant: 0.08,
          damping: 0.85,
          avoidOverlap: 0.7,
        },
        stabilization: {
          enabled: true,
          iterations: 150,
          updateInterval: 25,
        },
        minVelocity: 0.75,
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
      },
    };

    const network = new Network(containerRef.current, { nodes, edges: edgesData }, options);
    networkRef.current = network;

    // Freeze physics once layout stabilizes so the graph stays completely still
    network.once('stabilizationIterationsDone', () => {
      network.setOptions({ physics: { enabled: false } });
    });

    // Neighborhood highlight on click
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const selectedId = Number(params.nodes[0]);
        const connectedNodes = network.getConnectedNodes(selectedId) as number[];
        const allConnected = new Set([selectedId, ...connectedNodes]);

        // Dim non-connected nodes
        nodes.forEach((node: any) => {
          if (allConnected.has(node.id)) {
            nodes.update({
              id: node.id,
              color: { background: node.originalColor, border: '#0F172A' },
            });
          } else {
            nodes.update({
              id: node.id,
              color: { background: 'rgba(226, 232, 240, 0.3)', border: 'rgba(203, 213, 225, 0.3)' },
            });
          }
        });

        const targetClause = clauses.find((c) => c.index === selectedId);
        if (targetClause) {
          setSelectedNodeInfo({
            id: targetClause.index,
            label: targetClause.label,
            text: targetClause.text,
            risk: riskMap.get(targetClause.index) || 'LOW',
          });
          onSelectClause?.(targetClause.index);
        }
      } else {
        // Reset all nodes
        nodes.forEach((node: any) => {
          nodes.update({
            id: node.id,
            color: { background: node.originalColor, border: node.originalColor },
          });
        });
        setSelectedNodeInfo(null);
      }
    });

    return () => {
      network.destroy();
    };
  }, [clauses, visibleEdges, risks, contradictionPairs, highThreshold, mediumThreshold, onSelectClause]);

  const handleFit = () => {
    networkRef.current?.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
  };

  const handleZoomIn = () => {
    if (!networkRef.current) return;
    const scale = networkRef.current.getScale();
    networkRef.current.moveTo({ scale: scale * 1.25, animation: true });
  };

  const handleZoomOut = () => {
    if (!networkRef.current) return;
    const scale = networkRef.current.getScale();
    networkRef.current.moveTo({ scale: scale * 0.8, animation: true });
  };

  const handleStabilize = () => {
    if (!networkRef.current) return;
    networkRef.current.setOptions({ physics: { enabled: true } });
    networkRef.current.stabilize(150);
    networkRef.current.once('stabilizationIterationsDone', () => {
      networkRef.current?.setOptions({ physics: { enabled: false } });
    });
  };

  return (
    <div className="graph-container-card">
      <div className="graph-controls" style={{ flexWrap: 'wrap', gap: '0.85rem' }}>
        <div>
          <div className="section-heading" style={{ marginBottom: '0.15rem' }}>
            Interactive Document Knowledge Graph
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Nodes represent clauses; links show semantic similarity. Red dashed lines denote contradictions.
          </p>
        </div>

        {/* Edge Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Connection Slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#F1F5F9', padding: '0.3rem 0.65rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
            <SlidersHorizontal size={14} color="var(--text-muted)" />
            <span style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Threshold: {(edgeThreshold * 100).toFixed(0)}%
            </span>
            <input
              type="range"
              min="0.75"
              max="0.95"
              step="0.01"
              value={edgeThreshold}
              onChange={(e) => setEdgeThreshold(parseFloat(e.target.value))}
              style={{ width: '85px', accentColor: 'var(--accent)', cursor: 'pointer' }}
              title="Increase to decrease connection lines; decrease to show more connections"
            />
            <span className="pill pill-neutral" style={{ fontSize: '0.72rem', padding: '0.1rem 0.4rem' }}>
              {visibleEdges.length} Lines
            </span>
          </div>

          {/* Zoom & Fit Toolbar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <button className="btn btn-secondary" onClick={handleZoomIn} title="Zoom In" style={{ padding: '0.35rem 0.55rem' }}>
              <ZoomIn size={15} />
            </button>
            <button className="btn btn-secondary" onClick={handleZoomOut} title="Zoom Out" style={{ padding: '0.35rem 0.55rem' }}>
              <ZoomOut size={15} />
            </button>
            <button className="btn btn-secondary" onClick={handleFit} title="Fit to Screen" style={{ padding: '0.35rem 0.55rem' }}>
              <Maximize2 size={15} />
            </button>
            <button className="btn btn-secondary" onClick={handleStabilize} title="Re-stabilize Layout" style={{ padding: '0.35rem 0.55rem' }}>
              <RefreshCw size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Vis Network Canvas */}
      <div ref={containerRef} className="graph-canvas" />

      {/* Graph Legend & Status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginTop: '0.75rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.15rem' }}>
          <span><span className="legend-dot" style={{ backgroundColor: '#EF4444' }} />High Risk</span>
          <span><span className="legend-dot" style={{ backgroundColor: '#F59E0B' }} />Medium Risk</span>
          <span><span className="legend-dot" style={{ backgroundColor: '#10B981' }} />Low Risk</span>
          <span><span style={{ display: 'inline-block', width: '14px', height: '2px', backgroundColor: '#EF4444', borderStyle: 'dashed', marginRight: '0.35rem', verticalAlign: 'middle' }} />Contradiction</span>
        </div>

        <div style={{ color: 'var(--text-muted)' }}>
          Tip: Adjust the <strong>Threshold slider</strong> to reduce or increase connection density
        </div>
      </div>

      {/* Selected Node Drawer */}
      {selectedNodeInfo && (
        <div style={{ marginTop: '0.85rem', padding: '0.85rem 1rem', background: '#F8FAFC', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
              <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>Clause {selectedNodeInfo.id} Selected</span>
              <span className={`pill pill-${selectedNodeInfo.risk === 'HIGH' ? 'high' : selectedNodeInfo.risk === 'MEDIUM' ? 'med' : 'low'}`}>
                {selectedNodeInfo.risk} RISK
              </span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              {selectedNodeInfo.text.length > 280 ? `${selectedNodeInfo.text.slice(0, 280)}...` : selectedNodeInfo.text}
            </p>
          </div>
          <button className="btn btn-secondary" onClick={() => setSelectedNodeInfo(null)} style={{ padding: '0.25rem 0.55rem', fontSize: '0.75rem' }}>
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};
