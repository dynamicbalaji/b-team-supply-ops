import { useState, useEffect, useRef } from 'react'
import { showManualScript } from '../utils/printManualScript'
import { SCENARIOS } from '../constants/scenarios'

const API_URL = import.meta.env.VITE_API_URL

export default function Nav({ scenario, onScenarioChange, onStartScenario, onReset, theme, onThemeToggle }) {
  const [dropOpen, setDropOpen]           = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')
  const [statusDetail, setStatusDetail]   = useState('')
  const dropRef = useRef(null)
  const btnRef  = useRef(null)

  const s = SCENARIOS[scenario] || SCENARIOS.port_strike

  useEffect(() => {
    if (!API_URL) { setBackendStatus('manual'); setStatusDetail('VITE_API_URL not set'); return }
    fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(5000) })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(d => { setBackendStatus(d.status === 'ok' ? 'live' : 'error'); setStatusDetail(JSON.stringify(d)) })
      .catch(err => { setBackendStatus('manual'); setStatusDetail(err.message) })
  }, [])

  useEffect(() => {
    function handleClick(e) {
      if (dropRef.current && !dropRef.current.contains(e.target) &&
          btnRef.current  && !btnRef.current.contains(e.target)) setDropOpen(false)
    }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  const isLive     = backendStatus === 'live'
  const isChecking = backendStatus === 'checking'
  const statusColor = isLive ? '#39d98a' : isChecking ? '#888' : '#ffb340'
  const statusLabel = isChecking ? '○ CONNECTING' : isLive ? '● LIVE' : '● MANUAL'

  return (
    <nav className="nav">
      <div className="logo">
        <div className="logo-icon">⬡</div>
        ChainGuard<span style={{ color: '#00d4ff' }}>AI</span>
      </div>

      <div className="nav-alert">
        <div className="dot" />
        THREAT LEVEL: CRITICAL — P0 INCIDENT ACTIVE
      </div>

      <div className="nav-r">
        {/* Theme toggle */}
        <button
          className="theme-toggle"
          onClick={onThemeToggle}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label="Toggle theme"
        >
          <div className="theme-toggle-knob">{theme === 'dark' ? '🌙' : '☀'}</div>
        </button>

        {/* Dynamic per-scenario pills */}
        <div className="pill">{s.caseId}</div>
        <div className="pill" style={{ color: '#ffb340', borderColor: '#2a3820' }}>{s.window}</div>

        <div title={`API: ${API_URL || '(not set)'} — ${statusDetail}`} style={{
          display:'flex', alignItems:'center', gap:'4px', padding:'3px 8px',
          borderRadius:'4px', cursor:'default',
          border:`1px solid ${statusColor}44`, background:`${statusColor}11`,
        }}>
          <span style={{ fontSize:'9px', fontFamily:"'JetBrains Mono',monospace", color:statusColor, letterSpacing:'.05em' }}>
            {statusLabel}
          </span>
        </div>

        <button className="nbtn" ref={btnRef} onClick={() => setDropOpen(v => !v)}>⚙ DEMO CTRL</button>
        <button className="nbtn danger" onClick={onReset}>↺ RESET</button>
      </div>

      <div className={`drop${dropOpen ? ' open' : ''}`} ref={dropRef}>
        <div className="drop-title">Demo Controller</div>
        <div style={{
          padding:'6px 8px', marginBottom:'8px', borderRadius:'4px',
          background:`${statusColor}11`, border:`1px solid ${statusColor}33`,
          fontFamily:"'JetBrains Mono',monospace", fontSize:'9px', color:statusColor, lineHeight:'1.5',
        }}>
          <div>{isLive ? '● Live backend connected' : isChecking ? '○ Connecting…' : '● Manual mode'}</div>
          {API_URL
            ? <div style={{ color:'#556', marginTop:'2px' }}>{API_URL}</div>
            : <div style={{ color:'#ff3b5c', marginTop:'2px' }}>⚠ VITE_API_URL not set</div>}
        </div>
        <select className="dsel" value={scenario} onChange={e => onScenarioChange(e.target.value)}>
          <option value="port_strike">🔴 Port Strike — Long Beach</option>
          <option value="customs_delay">🟡 Customs Delay — Shanghai</option>
          <option value="supplier_breach">🟠 Supplier Bankruptcy — Taiwan</option>
        </select>
        <button className="dbtn" onClick={() => { setDropOpen(false); onStartScenario() }}>▶ Start Scenario</button>
        <button className="dbtn2" onClick={() => { setDropOpen(false); showManualScript() }}>📜 Manual Mode Script</button>
      </div>
    </nav>
  )
}
