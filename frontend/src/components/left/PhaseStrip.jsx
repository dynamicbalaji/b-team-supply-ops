const PHASES = [
  { id: 0, label: 'Crisis Detected' },
  { id: 1, label: 'Agents Active' },
  { id: 2, label: 'Negotiating' },
  { id: 3, label: 'Approved & Executing' },
  { id: 5, label: 'Resolved ✓' },
]

export default function PhaseStrip({ currentPhase }) {
  // Collapse phase 4 (executing) into phase 3 (approved) — no separate pulsing step
  const displayPhase = currentPhase === 4 ? 3 : currentPhase

  return (
    <div className="phase-bar">
      <div className="ph-lbl">Phase</div>
      <div className="phases">
        {PHASES.map((ph, idx) => {
          let cls = 'ph'
          if (ph.id < displayPhase)  cls = 'ph done'
          if (ph.id === displayPhase) cls = 'ph active'

          return (
            <span key={ph.id} style={{ display:'contents' }}>
              <div className={cls}>
                <div className="pi" />
                {ph.label}
              </div>
              {idx < PHASES.length - 1 && (
                <div className="ph-arrow">→</div>
              )}
            </span>
          )
        })}
      </div>
    </div>
  )
}
