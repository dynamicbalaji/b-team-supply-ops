import { useState, useEffect, useCallback } from 'react'
import { SCENARIOS } from '../../constants/scenarios'

const AGENT_COLOR  = { log:'#00d4ff', fin:'#39d98a', pro:'#ffb340', sal:'#9b5de5', risk:'#ff3b5c', orc:'#00d4ff' }
const AGENT_LABEL  = { log:'🔵 Logistics Agent', fin:'🟢 Finance Agent', pro:'🟠 Procurement Agent', sal:'🟣 Sales Agent', risk:'🔴 Risk Agent', orc:'🎯 Orchestrator' }
const AGENT_BG     = { log:'rgba(0,212,255,.04)', fin:'rgba(57,217,138,.04)', pro:'rgba(255,179,64,.04)', sal:'rgba(155,93,229,.04)', risk:'rgba(255,59,92,.04)', orc:'rgba(0,212,255,.04)' }
const AGENT_BORDER = { log:'rgba(0,212,255,.18)', fin:'rgba(57,217,138,.18)', pro:'rgba(255,179,64,.18)', sal:'rgba(155,93,229,.18)', risk:'rgba(255,59,92,.18)', orc:'rgba(0,212,255,.18)' }

const EMAIL_DELAYS = [0, 2200, 4800, 7500, 10500]

function useEmailReveal(isRunning, resolutionTime) {
  const [visibleEmails, setVisibleEmails] = useState(0)
  const [startedAt, setStartedAt]         = useState(null)
  const timerRefs = useState(() => [])[0]

  const reset = useCallback(() => {
    timerRefs.forEach(clearTimeout)
    timerRefs.length = 0
    setVisibleEmails(0)
    setStartedAt(null)
  }, [timerRefs])

  const start = useCallback(() => {
    timerRefs.forEach(clearTimeout)
    timerRefs.length = 0
    setVisibleEmails(0)
    const now = Date.now()
    setStartedAt(now)
    EMAIL_DELAYS.forEach((delay, idx) => {
      timerRefs.push(setTimeout(() => setVisibleEmails(idx + 1), delay))
    })
  }, [timerRefs])

  // Auto-start when isRunning flips true
  useEffect(() => {
    if (isRunning && !startedAt) start()
    if (!isRunning && !resolutionTime && !startedAt) reset()
  }, [isRunning]) // eslint-disable-line

  return { visibleEmails, start, reset }
}

export default function SplitTab({ scenario, messages, resolutionTime, costSaved, isRunning }) {
  const s  = SCENARIOS[scenario] || SCENARIOS.port_strike
  const sc = {
    trad: s.trad || { emails:[], penalty:'⏱ 72 HOURS — PENALTY TRIGGERED' },
    ai:   s.ai   || { resolution:'—', summary:'' },
  }

  const { visibleEmails, start: replayEmails } = useEmailReveal(isRunning, resolutionTime)

  const hasLiveMessages = messages && messages.length > 0
  const displayMessages = hasLiveMessages ? messages.filter(m => m.agent !== undefined) : []
  const aiTime          = resolutionTime || sc.ai.resolution
  const everStarted     = isRunning || !!resolutionTime || hasLiveMessages

  return (
    <div className="split">

      {/* ── Traditional — left ── */}
      <div className="sp trad">
        <div className="sp-hd">
          <div className="sp-title" style={{ color:'#ff3b5c' }}>📧 Traditional Process</div>
          <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
            <div className="sp-time slow">72:00:00</div>
            {/* Replay button — only shown after scenario has run at least once */}
            {everStarted && (
              <button
                onClick={replayEmails}
                title="Replay email sequence"
                style={{
                  background:'transparent', border:'1px solid #223040',
                  borderRadius:'4px', color:'#3d5a72', cursor:'pointer',
                  padding:'2px 7px', fontSize:'9px',
                  fontFamily:"'JetBrains Mono',monospace", letterSpacing:'.05em',
                  transition:'all .2s',
                }}
                onMouseEnter={e => { e.target.style.color='#7aa0be'; e.target.style.borderColor='#3d5a72' }}
                onMouseLeave={e => { e.target.style.color='#3d5a72'; e.target.style.borderColor='#223040' }}
              >
                ↺ replay
              </button>
            )}
          </div>
        </div>

        {!everStarted ? (
          /* Pre-run placeholder */
          <div style={{
            display:'flex', flexDirection:'column', alignItems:'center',
            justifyContent:'center', flex:1, gap:'8px', opacity:.35,
          }}>
            <div style={{ fontSize:'22px' }}>📧</div>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>
              Run a scenario to see
            </div>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>
              the traditional process
            </div>
          </div>
        ) : (
          <>
            {sc.trad.emails.map((email, i) => (
              visibleEmails > i ? (
                <div className="eml" key={i} style={{ opacity:0, animation:'fadein 0.5s forwards' }}>
                  <div className="er">
                    <span className="efrom">{email.from}</span>
                    <span className="etime">{email.time}</span>
                  </div>
                  <div className="esubj">{email.subj}</div>
                  <div className="ebody">{email.body}</div>
                </div>
              ) : (
                <div key={i} className="eml" style={{
                  opacity:.1, minHeight:'62px', background:'transparent',
                  border:'1px dashed #1d2d40',
                }} />
              )
            ))}
            {visibleEmails >= sc.trad.emails.length && (
              <div className="ebar">{sc.trad.penalty}</div>
            )}
          </>
        )}
      </div>

      {/* ── ChainGuard AI — right ── */}
      <div className="sp ai">
        <div className="sp-hd">
          <div className="sp-title" style={{ color:'#39d98a' }}>🤖 ChainGuard AI</div>
          <div className="sp-time fast">{everStarted ? aiTime : '—'}</div>
        </div>

        {!everStarted ? (
          <div style={{
            display:'flex', flexDirection:'column', alignItems:'center',
            justifyContent:'center', flex:1, gap:'8px', opacity:.35,
          }}>
            <div style={{ fontSize:'22px' }}>🤖</div>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>
              Run a scenario to see
            </div>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>
              the AI resolution
            </div>
          </div>
        ) : (
          <>
            {(hasLiveMessages || costSaved) && (
              <div className="ai-bar">
                ✅ {costSaved ? `RESOLVED IN ${aiTime} — saved ${costSaved}` : sc.ai.summary}
              </div>
            )}

            {displayMessages.length > 0 ? (
              displayMessages.map(msg => (
                <div key={msg.id} className="eml" style={{
                  background:  AGENT_BG[msg.agent]     || 'rgba(0,212,255,.04)',
                  borderColor: AGENT_BORDER[msg.agent] || 'rgba(0,212,255,.18)',
                  opacity:0, animation:'fadein 0.4s forwards',
                }}>
                  <div className="er">
                    <span className="efrom" style={{ color: AGENT_COLOR[msg.agent] || '#00d4ff' }}>
                      {AGENT_LABEL[msg.agent] || msg.from || msg.agent}
                    </span>
                    <span className="etime">{msg.time}</span>
                  </div>
                  {(() => {
                    const clean   = (msg.text || '').replace(/<[^>]+>/g, '')
                    const dotIdx  = clean.search(/[.!?]/)
                    const subj    = dotIdx > 0 && dotIdx < 80 ? clean.slice(0, dotIdx + 1) : clean.slice(0, 60)
                    const body    = dotIdx > 0 && dotIdx < 80 ? clean.slice(dotIdx + 1).trim() : clean.slice(60).trim()
                    return (
                      <>
                        <div className="esubj" style={{ color:'#ddeeff' }}>{subj}</div>
                        {body && <div className="ebody" style={{ color:'#7aa0be' }}>{body}</div>}
                      </>
                    )
                  })()}
                  {msg.tools?.length > 0 && (
                    <div style={{ marginTop:'4px', display:'flex', flexWrap:'wrap', gap:'3px' }}>
                      {msg.tools.map((t, i) => <span key={i} className="tool-pill">{t}</span>)}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="eml" style={{ background:'rgba(0,212,255,.04)', borderColor:'rgba(0,212,255,.18)', opacity:.5 }}>
                <div className="er">
                  <span className="efrom" style={{ color:'#00d4ff' }}>🔵 Logistics Agent</span>
                  <span className="etime">--:--</span>
                </div>
                <div className="esubj" style={{ color:'#3d5a72' }}>
                  {isRunning ? 'Agents processing…' : 'Awaiting scenario start…'}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
