import { useRef, useCallback, useState } from 'react'
import { useLeafletMap, TILE_LAYERS } from '../../hooks/useLeafletMap'
import { SCENARIOS } from '../../constants/scenarios'
import PhaseStrip from './PhaseStrip'

export default function MapTab({
  scenario,
  mapRoute,
  mapStatus,
  mapStatusColor,
  truckPhase,
  onTruckPhaseChange,
  phase,
  isActive,
}) {
  const containerRef = useRef(null)
  const s = SCENARIOS[scenario] || SCENARIOS.port_strike
  const [tileLayerId, setTileLayerId] = useState('satellite')
  const [expanded, setExpanded] = useState(false)

  const handleTruckPhaseChange = useCallback(
    (newPhase) => onTruckPhaseChange(newPhase),
    [onTruckPhaseChange]
  )

  useLeafletMap(containerRef, {
    scenario,
    truckPhase,
    onTruckPhaseChange: handleTruckPhaseChange,
    isActive,
    tileLayerId,
  })

  const activeLayer = TILE_LAYERS[tileLayerId]

  return (
    <div className={`mapwrap layer-${tileLayerId}`}>
      <div className="map-bar">
        <div className="mbi">
          <div className="mbi-lbl">Origin</div>
          <div className="mbi-val" style={{ color:'#7aa0be' }}>{s.origin}</div>
        </div>
        <div className="mbi">
          <div className="mbi-lbl">Blocked At</div>
          <div className="mbi-val" style={{ color:'#ff3b5c' }}>{s.blockedAt}</div>
        </div>
        <div className="mbi">
          <div className="mbi-lbl">Active Route</div>
          <div className="mbi-val" style={{ color:'#00d4ff' }}>{mapRoute}</div>
        </div>
        <div className="mbi">
          <div className="mbi-lbl">Status</div>
          <div className="mbi-val" style={{ color:mapStatusColor }}>{mapStatus}</div>
        </div>
      </div>

      <div
        ref={containerRef}
        style={{ position:'absolute', top:'46px', bottom:'36px', left:0, right:0, zIndex:1 }}
      />

      {/* Layer switcher — bottom-left, collapsible */}
      <div style={{
        position: 'absolute',
        bottom: '48px',
        left: '10px',
        zIndex: 900,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: '2px',
      }}>

        {/* Expandable layer list — slides up from toggle */}
        {expanded && (
          <div className="map-layer-panel">
            <div className="map-layer-header">
              <span className="map-layer-title">Map Layer</span>
            </div>
            {Object.values(TILE_LAYERS).map(layer => {
              const active = tileLayerId === layer.id
              return (
                <button
                  key={layer.id}
                  className={`map-layer-btn${active ? ' map-layer-btn--active' : ''}`}
                  onClick={() => { setTileLayerId(layer.id); setExpanded(false) }}
                >
                  <span className="map-layer-icon">{layer.icon}</span>
                  <span className="map-layer-label">{layer.label}</span>
                  {active && <span className="map-layer-dot" />}
                </button>
              )
            })}
          </div>
        )}

        {/* Toggle pill — always visible */}
        <button
          className={`map-layer-toggle${expanded ? ' map-layer-toggle--open' : ''}`}
          onClick={() => setExpanded(v => !v)}
          title="Toggle map layers"
        >
          <span className="map-layer-toggle-icon">{activeLayer.icon}</span>
          <span className="map-layer-toggle-label">{activeLayer.label}</span>
          <span className="map-layer-toggle-arrow">{expanded ? '▼' : '▲'}</span>
        </button>
      </div>

      <PhaseStrip currentPhase={phase} />
    </div>
  )
}
