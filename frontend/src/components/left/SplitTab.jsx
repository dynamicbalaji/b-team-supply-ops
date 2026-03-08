import { useState, useEffect, useCallback, useRef } from 'react'
import { SCENARIOS } from '../../constants/scenarios'

const AGENT_COLOR  = { log:'var(--acc)', fin:'var(--grn)', pro:'var(--orn)', sal:'var(--pur)', risk:'var(--red)', orc:'var(--acc)' }
const AGENT_LABEL  = { log:'🔵 Logistics Agent', fin:'🟢 Finance Agent', pro:'🟠 Procurement Agent', sal:'🟣 Sales Agent', risk:'🔴 Risk Agent', orc:'🎯 Orchestrator' }
const AGENT_BG     = { log:'var(--bub-log-bg)', fin:'var(--bub-fin-bg)', pro:'var(--bub-pro-bg)', sal:'var(--bub-sal-bg)', risk:'var(--bub-risk-bg)', orc:'var(--bub-orc-bg)' }
// For border colors, we'll create a subtle version of the main colors using CSS calc or fallback to main colors
const AGENT_BORDER = { log:'var(--acc)', fin:'var(--grn)', pro:'var(--orn)', sal:'var(--pur)', risk:'var(--red)', orc:'var(--acc)' }

// Traditional: slow — one email every ~2s
const TRAD_DELAYS = [0, 2200, 4800, 7500, 10800]
// AI: fast — one message every 420ms
const aiDelay = (i) => i * 420

function formatCost(raw) {
  if (raw == null) return null
  const num = typeof raw === 'number' ? raw : Number(String(raw).replace(/[$,]/g, ''))
  if (isNaN(num)) return String(raw)
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(1)}M`
  if (num >= 1_000)     return `$${Math.round(num / 1000)}K`
  return `$${num}`
}

export default function SplitTab({ scenario, messages, resolutionTime, costSaved, isRunning }) {
  const s  = SCENARIOS[scenario] || SCENARIOS.port_strike
  const sc = {
    trad: s.trad || { emails: [], penalty: '⏱ 72 HOURS — PENALTY TRIGGERED' },
    ai:   s.ai   || { resolution: '—', summary: '' },
  }

  const [visibleTrad, setVisibleTrad] = useState(0)
  const [visibleAI,   setVisibleAI]   = useState(0)
  const [replaying,   setReplaying]   = useState(false)
  const timers     = useRef([])
  const startedRef = useRef(false)

  const hasLiveMessages = messages && messages.length > 0
  const displayMessages = hasLiveMessages ? messages.filter(m => m.agent !== undefined) : []
  const aiTime          = resolutionTime || sc.ai.resolution
  const everStarted     = isRunning || !!resolutionTime || hasLiveMessages

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }, [])

  const runReplay = useCallback((msgs) => {
    clearTimers()
    setVisibleTrad(0)
    setVisibleAI(0)
    setReplaying(true)

    // Traditional emails — slow drip
    TRAD_DELAYS.forEach((delay, i) => {
      timers.current.push(setTimeout(() => setVisibleTrad(i + 1), delay))
    })

    // AI messages — fast burst
    msgs.forEach((_, i) => {
      timers.current.push(setTimeout(() => setVisibleAI(i + 1), aiDelay(i)))
    })

    const total = Math.max(
      TRAD_DELAYS[TRAD_DELAYS.length - 1] + 600,
      msgs.length > 0 ? aiDelay(msgs.length - 1) + 600 : 600
    )
    timers.current.push(setTimeout(() => setReplaying(false), total))
  }, [clearTimers])

  // On mount: always start traditional emails immediately so tab is never empty
  useEffect(() => {
    startedRef.current = true
    if (hasLiveMessages || resolutionTime) {
      // Scenario already done — replay everything
      runReplay(displayMessages)
    } else {
      // No scenario yet — just drip traditional emails as a preview
      TRAD_DELAYS.forEach((delay, i) => {
        timers.current.push(setTimeout(() => setVisibleTrad(i + 1), delay))
      })
    }
    return () => clearTimers()
  }, []) // eslint-disable-line

  // When scenario starts running, restart full replay
  useEffect(() => {
    if (isRunning) {
      runReplay(displayMessages.length > 0 ? displayMessages : [])
    }
    if (!isRunning && !resolutionTime && !hasLiveMessages) {
      clearTimers()
      setVisibleTrad(0)
      setVisibleAI(0)
      // Restart trad email preview
      TRAD_DELAYS.forEach((delay, i) => {
        timers.current.push(setTimeout(() => setVisibleTrad(i + 1), delay))
      })
    }
  }, [isRunning]) // eslint-disable-line

  // As new AI messages arrive mid-run, extend visibility
  useEffect(() => {
    if (startedRef.current && displayMessages.length > visibleAI) {
      setVisibleAI(displayMessages.length)
    }
  }, [displayMessages.length]) // eslint-disable-line

  const handleReplay = () => runReplay(displayMessages)

  return (
    <div style={{ display:'flex', flexDirection:'column', flex:1, minHeight:0 }}>

      {/* ── Shared replay bar ── */}
      <div style={{
        display:'flex', justifyContent:'space-between', alignItems:'center',
        padding:'5px 14px', borderBottom:'1px solid var(--bdr)',
        background:'var(--bg)', flexShrink:0,
      }}>
        <div style={{ display:'flex', gap:'14px' }}>
          <span style={{ fontSize:'9px', fontFamily:"'JetBrains Mono',monospace", color:'var(--red)', opacity:.8 }}>
            🐌 Traditional: ~12s / step
          </span>
          <span style={{ fontSize:'9px', fontFamily:"'JetBrains Mono',monospace", color:'var(--grn)', opacity:.8 }}>
            ⚡ AI: ~0.4s / step
          </span>
        </div>
        <button
          onClick={handleReplay}
          disabled={replaying}
          style={{
            background:'transparent', border:`1px solid ${replaying ? 'var(--bdr)' : 'var(--bdr)'}`,
            borderRadius:'4px', color: replaying ? 'var(--t3)' : 'var(--t2)',
            cursor: replaying ? 'not-allowed' : 'pointer',
            padding:'3px 10px', fontSize:'9px',
            fontFamily:"'JetBrains Mono',monospace", letterSpacing:'.08em', transition:'all .2s',
          }}
          onMouseEnter={e => { if (!replaying) e.currentTarget.style.cssText += 'color:var(--acc);border-color:var(--acc);' }}
          onMouseLeave={e => { if (!replaying) e.currentTarget.style.cssText += 'color:var(--t2);border-color:var(--bdr);' }}
        >
          {replaying ? '⏵ replaying…' : '↺ REPLAY BOTH PANELS'}
        </button>
      </div>

      <div className="split">

        {/* ── Traditional — left ── */}
        <div className="sp trad">
          <div className="sp-hd">
            <div className="sp-title" style={{ color:'var(--red)' }}>📧 Traditional Process</div>
            <div className="sp-time slow">72:00:00</div>
          </div>

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
              <div key={i} className="eml" style={{
                opacity:.08, minHeight:'62px', background:'transparent',
                border:'1px dashed var(--bdr)',
              }} />
            )
          ))}

          {visibleTrad >= sc.trad.emails.length && (
            <div className="ebar">{sc.trad.penalty}</div>
          )}
        </div>

        {/* ── ChainGuard AI — right ── */}
        <div className="sp ai">
          <div className="sp-hd">
            <div className="sp-title" style={{ color:'var(--grn)' }}>🤖 ChainGuard AI</div>
            <div className="sp-time fast">{everStarted ? aiTime : '—'}</div>
          </div>

          {!everStarted ? (
            <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', flex:1, gap:'8px', paddingTop:'40px' }}>
              <div style={{ fontSize:'22px',opacity:.35, }}>🤖</div>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'11px' }}  className="msg-empty-txt">
                Start a scenario to see<br/>the AI resolution
              </div>
            </div>
          ) : (
            <>
              {(costSaved || resolutionTime) && (
                <div className="ai-bar">
                  ✅ {costSaved
                    ? `RESOLVED IN ${aiTime} — saved ${formatCost(costSaved)}`
                    : sc.ai.summary}
                </div>
              )}

              {displayMessages.length > 0 ? (
                displayMessages.slice(0, visibleAI).map(msg => (
                  <div key={msg.id} className="eml" style={{
                    background:  AGENT_BG[msg.agent]     || 'var(--bub-log-bg)',
                    borderColor: AGENT_BORDER[msg.agent] || 'var(--acc)',
                    opacity:0, animation:'fadein 0.35s forwards',
                  }}>
                    <div className="er">
                      <span className="efrom" style={{ color: AGENT_COLOR[msg.agent] || 'var(--acc)' }}>
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
                          <div className="esubj">{subj}</div>
                          {body && <div className="ebody">{body}</div>}
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
                <div className="eml" style={{ background:'var(--bub-log-bg)', borderColor:'var(--acc)', opacity:.5 }}>
                  <div className="er">
                    <span className="efrom" style={{ color:'var(--acc)' }}>🔵 Logistics Agent</span>
                    <span className="etime">--:--</span>
                  </div>
                  <div className="esubj">
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
