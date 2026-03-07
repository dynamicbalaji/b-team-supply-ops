import { SCENARIOS } from '../../constants/scenarios'

const AGENT_COLOR = {
  log: '#00d4ff', fin: '#39d98a', pro: '#ffb340',
  sal: '#9b5de5', risk: '#ff3b5c', orc: '#00d4ff',
}
const AGENT_LABEL = {
  log: '🔵 Logistics Agent', fin: '🟢 Finance Agent',
  pro: '🟠 Procurement Agent', sal: '🟣 Sales Agent',
  risk: '🔴 Risk Agent', orc: '🎯 Orchestrator',
}
const AGENT_BG = {
  log: 'rgba(0,212,255,.04)',    fin: 'rgba(57,217,138,.04)',
  pro: 'rgba(255,179,64,.04)',   sal: 'rgba(155,93,229,.04)',
  risk: 'rgba(255,59,92,.04)',   orc: 'rgba(0,212,255,.04)',
}
const AGENT_BORDER = {
  log: 'rgba(0,212,255,.18)',    fin: 'rgba(57,217,138,.18)',
  pro: 'rgba(255,179,64,.18)',   sal: 'rgba(155,93,229,.18)',
  risk: 'rgba(255,59,92,.18)',   orc: 'rgba(0,212,255,.18)',
}

export default function SplitTab({ scenario, messages, resolutionTime, costSaved }) {
  const s = SCENARIOS[scenario] || SCENARIOS.port_strike

  // Use live messages if available, otherwise show scenario static summary cards
  const hasLiveMessages = messages && messages.length > 0
  // Filter out pure orchestrator broadcast messages for cleaner display
  const displayMessages = hasLiveMessages
    ? messages.filter(m => m.agent !== undefined)
    : []

  const aiTime = resolutionTime || s.ai.resolution

  return (
    <div className="split">

      {/* ── Traditional — left ── */}
      <div className="sp trad">
        <div className="sp-hd">
          <div className="sp-title" style={{ color:'#ff3b5c' }}>📧 Traditional Process</div>
          <div className="sp-time slow">72:00:00</div>
        </div>

        {s.trad.emails.map((email, i) => (
          <div className="eml" key={i}>
            <div className="er">
              <span className="efrom">{email.from}</span>
              <span className="etime">{email.time}</span>
            </div>
            <div className="esubj">{email.subj}</div>
            <div className="ebody">{email.body}</div>
          </div>
        ))}

        <div className="ebar">{s.trad.penalty}</div>
      </div>

      {/* ── ChainGuard AI — right ── */}
      <div className="sp ai">
        <div className="sp-hd">
          <div className="sp-title" style={{ color:'#39d98a' }}>🤖 ChainGuard AI</div>
          <div className="sp-time fast">{aiTime}</div>
        </div>

        {/* Summary bar — live data when available */}
        {(hasLiveMessages || costSaved) && (
          <div className="ai-bar">
            ✅ {costSaved
              ? `RESOLVED IN ${aiTime} — saved ${costSaved}`
              : s.ai.summary}
          </div>
        )}

        {/* Live messages from scenario run */}
        {displayMessages.length > 0 ? (
          displayMessages.map(msg => (
            <div
              key={msg.id}
              className="eml"
              style={{
                background:   AGENT_BG[msg.agent]     || 'rgba(0,212,255,.04)',
                borderColor:  AGENT_BORDER[msg.agent] || 'rgba(0,212,255,.18)',
              }}
            >
              <div className="er">
                <span className="efrom" style={{ color: AGENT_COLOR[msg.agent] || '#00d4ff' }}>
                  {AGENT_LABEL[msg.agent] || msg.from || msg.agent}
                </span>
                <span className="etime">{msg.time}</span>
              </div>
              {/* First sentence as subject, rest as body */}
              {(() => {
                const clean = msg.text.replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]+>/g, '')
                const dotIdx = clean.search(/[.!?]/)
                const subj = dotIdx > 0 && dotIdx < 80 ? clean.slice(0, dotIdx + 1) : clean.slice(0, 60)
                const body = dotIdx > 0 && dotIdx < 80 ? clean.slice(dotIdx + 1).trim() : clean.slice(60).trim()
                return (
                  <>
                    <div className="esubj" style={{ color:'#ddeeff' }}>{subj}</div>
                    {body && <div className="ebody" style={{ color:'#7aa0be' }}>{body}</div>}
                  </>
                )
              })()}
              {msg.tools?.length > 0 && (
                <div style={{ marginTop:'4px', display:'flex', flexWrap:'wrap', gap:'3px' }}>
                  {msg.tools.map((t, i) => (
                    <span key={i} className="tool-pill">{t}</span>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          /* Static placeholder cards before scenario runs */
          <>
            <div className="eml" style={{ background:'rgba(0,212,255,.04)', borderColor:'rgba(0,212,255,.18)', opacity:.5 }}>
              <div className="er">
                <span className="efrom" style={{ color:'#00d4ff' }}>🔵 Logistics Agent</span>
                <span className="etime">--:--</span>
              </div>
              <div className="esubj" style={{ color:'#3d5a72' }}>Awaiting scenario start…</div>
            </div>
          </>
        )}
      </div>

    </div>
  )
}
