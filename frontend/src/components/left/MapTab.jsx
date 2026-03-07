import { useRef, useCallback } from 'react'
import { useLeafletMap } from '../../hooks/useLeafletMap'
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

  const handleTruckPhaseChange = useCallback(
    (newPhase) => onTruckPhaseChange(newPhase),
    [onTruckPhaseChange]
  )

  useLeafletMap(containerRef, {
    scenario,
    truckPhase,
    onTruckPhaseChange: handleTruckPhaseChange,
    isActive,
  })

  return (
    <div className="mapwrap">
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

      <PhaseStrip currentPhase={phase} />
    </div>
  )
}
