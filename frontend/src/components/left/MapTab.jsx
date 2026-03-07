export default function MapTab({ isActive }) {
  return (
    <div className="mapwrap">
      {/* Map info bar */}
      <div className="map-bar">
        <div className="mbi">
          <div className="mbi-lbl">Origin</div>
          <div className="mbi-val" style={{ color: '#7aa0be' }}>📦 Shanghai Port</div>
        </div>
        <div className="mbi">
          <div className="mbi-lbl">Blocked At</div>
          <div className="mbi-val" style={{ color: '#ff3b5c' }}>🔴 Long Beach</div>
        </div>
        <div className="mbi">
          <div className="mbi-lbl">Active Route</div>
          <div className="mbi-val" style={{ color: '#00d4ff' }}>— Awaiting agents</div>
        </div>
        <div className="mbi">
          <div className="mbi-lbl">Status</div>
          <div className="mbi-val" style={{ color: '#ffb340' }}>STANDBY</div>
        </div>
      </div>

      {/* Canvas — will be animated in Phase 2 */}
      <canvas
        id="mapCanvas"
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
      />

      {/* Phase strip */}
      <div className="phase-bar">
        <div className="ph-lbl">Phase</div>
        <div className="phases">
          <div className="ph" id="ph0">
            <div className="pi" />
            Crisis Detected
          </div>
          <div className="ph-arrow">→</div>
          <div className="ph" id="ph1">
            <div className="pi" />
            Agents Active
          </div>
          <div className="ph-arrow">→</div>
          <div className="ph" id="ph2">
            <div className="pi" />
            Negotiating
          </div>
          <div className="ph-arrow">→</div>
          <div className="ph" id="ph3">
            <div className="pi" />
            Approved
          </div>
          <div className="ph-arrow">→</div>
          <div className="ph" id="ph4">
            <div className="pi" />
            Executing
          </div>
        </div>
      </div>
    </div>
  )
}
