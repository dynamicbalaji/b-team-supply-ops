const AGENT_META = {
  log: { label:'LOGISTICS',   colorClass:'al' },
  fin: { label:'FINANCE',     colorClass:'af' },
  pro: { label:'PROCUREMENT', colorClass:'ap' },
  sal: { label:'SALES',       colorClass:'as_' },
}

export default function AgentCard({ id, data }) {
  const meta = AGENT_META[id] ?? { label:id.toUpperCase(), colorClass:'al' }
  const {
    status      = 'STANDBY',
    statusClass = 'idle',
    confidence  = 0,
    tool        = 'idle',
    pulseOn     = false,
  } = data ?? {}

  return (
    <div className={`agcard ${meta.colorClass}`}>
      <div className="ag-hd">
        <span className="ag-name">{meta.label}</span>
        <span className={`ag-pulse${pulseOn ? ' on' : ''}`} />
      </div>

      <div className={`ag-status ${statusClass}`}>{status}</div>

      <div className="confrow">
        <div className="confbg">
          <div
            className="conffill"
            style={{
              width: `${confidence}%`,
              transition: 'width 1.2s ease',
            }}
          />
        </div>
        <span className="confval">{confidence > 0 ? `${confidence}%` : '—'}</span>
      </div>

      {tool && tool !== 'idle' && (
        <div className="tool-pill">{tool}</div>
      )}
    </div>
  )
}
