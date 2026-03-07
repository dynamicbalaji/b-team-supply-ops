const PHASES = [
  { id: 0, label: 'Crisis Detected' },
  { id: 1, label: 'Agents Active' },
  { id: 2, label: 'Negotiating' },
  { id: 3, label: 'Approved' },
  { id: 4, label: 'Executing' },
]

export default function PhaseStrip({ currentPhase }) {
  return (
    <div className="phase-bar">
      <div className="ph-lbl">Phase</div>
      <div className="phases">
        {PHASES.map((ph, idx) => {
          let cls = 'ph'
          if (ph.id < currentPhase)  cls = 'ph done'
          if (ph.id === currentPhase) cls = 'ph active'

          return (
            <span key={ph.id} style={{ display: 'contents' }}>
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
