import { useEffect, useRef } from 'react'

const AGENT_META = {
  log: { label: 'LOGISTICS',   colorClass: 'al',  color: '#00d4ff' },
  fin: { label: 'FINANCE',     colorClass: 'af',  color: '#39d98a' },
  pro: { label: 'PROCUREMENT', colorClass: 'ap',  color: '#ffb340' },
  sal: { label: 'SALES',       colorClass: 'as_', color: '#9b5de5' },
}

export default function AgentCard({ id, data }) {
  const meta = AGENT_META[id] ?? { label: id.toUpperCase(), colorClass: 'al', color: '#00d4ff' }
  const {
    status      = 'STANDBY',
    statusClass = 'idle',
    confidence  = 0,
    tool        = 'idle',
    pulseOn     = false,
  } = data ?? {}

  // Animate confidence bar: set 0 first, then target on next frame
  const fillRef     = useRef(null)
  const prevConfRef = useRef(0)

  useEffect(() => {
    if (!fillRef.current) return
    const el = fillRef.current
    if (confidence !== prevConfRef.current) {
      // Force reflow at current width before transitioning
      el.style.transition = 'none'
      void el.offsetWidth
      el.style.transition = 'width 1.2s ease'
      el.style.width = `${confidence}%`
      prevConfRef.current = confidence
    }
  }, [confidence])

  return (
    <div className={`agcard ${meta.colorClass}`}>
      {/* Label + pulse dot */}
      <div className="ag-hd">
        <span className="ag-name">{meta.label}</span>
        <span className={`ag-pulse${pulseOn ? ' on' : ''}`} />
      </div>

      {/* Status */}
      <div className={`ag-status ${statusClass}`}>{status}</div>

      {/* Confidence bar */}
      <div className="confrow">
        <div className="confbg">
          <div
            ref={fillRef}
            className="conffill"
            style={{ width: `${confidence}%` }}
          />
        </div>
        <span className="confval">{confidence > 0 ? `${confidence}%` : '—'}</span>
      </div>

      {/* Active tool pill */}
      {tool && tool !== 'idle' && (
        <div className="tool-pill">{tool}</div>
      )}
    </div>
  )
}
