const AGENT_META = {
  log: { label:'LOGISTICS',   colorClass:'al',  color:'#00d4ff' },
  fin: { label:'FINANCE',     colorClass:'af',  color:'#39d98a' },
  pro: { label:'PROCUREMENT', colorClass:'ap',  color:'#ffb340' },
  sal: { label:'SALES',       colorClass:'as_', color:'#9b5de5' },
}

export default function AgentCard({ id, data }) {
  const meta = AGENT_META[id] ?? { label:id.toUpperCase(), colorClass:'al', color:'#00d4ff' }
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
