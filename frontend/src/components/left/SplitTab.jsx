import { useState, useEffect, useCallback, useRef } from 'react'
import { SCENARIOS } from '../../constants/scenarios'

const AGENT_COLOR  = { log:'#00d4ff', fin:'#39d98a', pro:'#ffb340', sal:'#9b5de5', risk:'#ff3b5c', orc:'#00d4ff' }
const AGENT_LABEL  = { log:'🔵 Logistics Agent', fin:'🟢 Finance Agent', pro:'🟠 Procurement Agent', sal:'🟣 Sales Agent', risk:'🔴 Risk Agent', orc:'🎯 Orchestrator' }
const AGENT_BG     = { log:'rgba(0,212,255,.04)', fin:'rgba(57,217,138,.04)', pro:'rgba(255,179,64,.04)', sal:'rgba(155,93,229,.04)', risk:'rgba(255,59,92,.04)', orc:'rgba(0,212,255,.04)' }
const AGENT_BORDER = { log:'rgba(0,212,255,.18)', fin:'rgba(57,217,138,.18)', pro:'rgba(255,179,64,.18)', sal:'rgba(155,93,229,.18)', risk:'rgba(255,59,92,.18)', orc:'rgba(0,212,255,.18)' }

// Traditional: painfully slow — one email every ~2s, dragging out to 12s total
const TRAD_DELAYS = [0, 2200, 4800, 7500, 10800]

// AI: blazing fast — all messages within 3s total, ~400ms apart
const aiDelay = (i) => i * 420

export default function SplitTab({ scenario, messages, resolutionTime, costSaved, isRunning }) {
  const s  = SCENARIOS[scenario] || SCENARIOS.port_strike
  const sc = {
    trad: s.trad || { emails: [], penalty: '⏱ 72 HOURS — PENALTY TRIGGERED' },
    ai:   s.ai   || { resolution: '—', summary: '' },
  }

  const [visibleTrad, setVisibleTrad] = useState(0)   // how many trad emails visible
  const [visibleAI,   setVisibleAI]   = useState(0)   // how many AI messages visible
  const [replaying,   setReplaying]   = useState(false)
  const timers   = useRef([])
  const startedRef = useRef(false)

  const hasLiveMessages = messages && messages.length > 0
  const displayMessages = hasLiveMessages ? messages.filter(m => m.agent !== undefined) : []
  const aiTime      = resolutionTime || sc.ai.resolution
  const everStarted = isRunning || !!resolutionTime || hasLiveMessages

  const clearTimers = () => { timers.current.forEach(clearTimeout); timers.current = [] }

  const runReplay = useCallback((msgs) => {
    clearTimers()
    setVisibleTrad(0)
    setVisibleAI(0)
    setReplaying(true)

    // Schedule traditional emails — slow
    TRAD_DELAYS.forEach((delay, i) => {
      timers.current.push(setTimeout(() => setVisibleTrad(i + 1), delay))
    })

    // Schedule AI messages — fast (all done before 3rd trad email appears)
    msgs.forEach((_, i) => {
      timers.current.push(setTimeout(() => setVisibleAI(i + 1), aiDelay(i)))
    })

    // Mark replay done after all timers
    const total = Math.max(
      TRAD_DELAYS[TRAD_DELAYS.length - 1] + 600,
      aiDelay(msgs.length - 1) + 600
    )
    timers.current.push(setTimeout(() => setReplaying(false), total))
  }, [])

  // Auto-run when scenario first starts
  useEffect(() => {
    if (isRunning && !startedRef.current) {
      startedRef.current = true
      runReplay(displayMessages.length > 0 ? displayMessages : [])
    }
    if (!isRunning && !resolutionTime) {
      startedRef.current = false
      clearTimers()
      setVisibleTrad(0)
      setVisibleAI(0)
    }
  }, [isRunning]) // eslint-disable-line

  // When messages arrive mid-run, extend AI visibility to cover new ones
  useEffect(() => {
    if (startedRef.current && displayMessages.length > visibleAI) {
      setVisibleAI(displayMessages.length)
    }
  }, [displayMessages.length]) // eslint-disable-line

  const handleReplay = () => runReplay(displayMessages)

  return (
    <div style={{ display:'flex', flexDirection:'column', flex:1, minHeight:0 }}>

      {/* ── Shared replay bar ── */}
      {everStarted && (
        <div style={{
          display:'flex', justifyContent:'space-between', alignItems:'center',
          padding:'5px 14px', borderBottom:'1px solid #1d2d40',
          background:'#090e15', flexShrink:0,
        }}>
          {/* Speed legend */}
          <div style={{ display:'flex', gap:'14px' }}>
            <span style={{ fontSize:'9px', fontFamily:"'JetBrains Mono',monospace", color:'#ff3b5c', opacity:.7 }}>
              🐌 Traditional: ~12s / step
            </span>
            <span style={{ fontSize:'9px', fontFamily:"'JetBrains Mono',monospace", color:'#39d98a', opacity:.7 }}>
              ⚡ AI: ~0.4s / step
            </span>
          </div>
          <button
            onClick={handleReplay}
            disabled={replaying}
            style={{
              display:'flex', alignItems:'center', gap:'5px',
              background: replaying ? 'transparent' : 'transparent',
              border:`1px solid ${replaying ? '#1d2d40' : '#1d2d40'}`,
              borderRadius:'4px',
              color: replaying ? '#3d5a72' : '#7aa0be',
              cursor: replaying ? 'not-allowed' : 'pointer',
              padding:'3px 10px', fontSize:'9px',
              fontFamily:"'JetBrains Mono',monospace", letterSpacing:'.08em',
              transition:'all .2s',
            }}
            onMouseEnter={e => { if (!replaying) e.currentTarget.style.cssText += 'color:#00d4ff;border-color:#00d4ff55;' }}
            onMouseLeave={e => { if (!replaying) e.currentTarget.style.cssText += 'color:#7aa0be;border-color:#1d2d40;' }}
          >
            {replaying ? '⏵ replaying…' : '↺ REPLAY BOTH PANELS'}
          </button>
        </div>
      )}

      <div className="split">

        {/* ── Traditional — left ── */}
        <div className="sp trad">
          <div className="sp-hd">
            <div className="sp-title" style={{ color:'#ff3b5c' }}>📧 Traditional Process</div>
            <div className="sp-time slow">72:00:00</div>
          </div>

          {!everStarted ? (
            <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', flex:1, gap:'8px', opacity:.35 }}>
              <div style={{ fontSize:'22px' }}>📧</div>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>Run a scenario to see</div>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>the traditional process</div>
            </div>
          ) : (
            <>
              {sc.trad.emails.map((email, i) => (
                visibleTrad > i ? (
                  <div className="eml" key={i} style={{ opacity:0, animation:'fadein 0.5s forwards' }}>
                    <div className="er">
                      <span className="efrom">{email.from}</span>
                      <span className="etime">{email.time}</span>
                    </div>
                    <div className="esubj">{email.subj}</div>
                    <div className="ebody">{email.body}</div>
                  </div>
                ) : (
                  <div key={i} className="eml" style={{ opacity:.1, minHeight:'62px', background:'transparent', border:'1px dashed #1d2d40' }} />
                )
              ))}
              {visibleTrad >= sc.trad.emails.length && (
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
            <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', flex:1, gap:'8px', opacity:.35 }}>
              <div style={{ fontSize:'22px' }}>🤖</div>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>Run a scenario to see</div>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>the AI resolution</div>
            </div>
          ) : (
            <>
              {(costSaved || (!replaying && hasLiveMessages)) && (
                <div className="ai-bar">
                  ✅ {costSaved ? `RESOLVED IN ${aiTime} — saved ${costSaved}` : sc.ai.summary}
                </div>
              )}

              {displayMessages.length > 0 ? (
                displayMessages.slice(0, visibleAI).map(msg => (
                  <div key={msg.id} className="eml" style={{
                    background:  AGENT_BG[msg.agent]     || 'rgba(0,212,255,.04)',
                    borderColor: AGENT_BORDER[msg.agent] || 'rgba(0,212,255,.18)',
                    opacity:0, animation:'fadein 0.35s forwards',
                  }}>
                    <div className="er">
                      <span className="efrom" style={{ color: AGENT_COLOR[msg.agent] || '#00d4ff' }}>
                        {AGENT_LABEL[msg.agent] || msg.from || msg.agent}
                      </span>
                      <span className="etime">{msg.time}</span>
                    </div>
                    {(() => {
                      const clean  = (msg.text || '').replace(/<[^>]+>/g, '')
                      const dotIdx = clean.search(/[.!?]/)
                      const subj   = dotIdx > 0 && dotIdx < 80 ? clean.slice(0, dotIdx + 1) : clean.slice(0, 60)
                      const body   = dotIdx > 0 && dotIdx < 80 ? clean.slice(dotIdx + 1).trim() : clean.slice(60).trim()
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
    </div>
  )
}
