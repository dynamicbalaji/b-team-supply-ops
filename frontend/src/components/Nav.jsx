import { useState, useEffect, useRef } from 'react'

export default function Nav({ scenario, onScenarioChange, onStartScenario, onReset, onManualScript }) {
  const [dropOpen, setDropOpen]         = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')
  const dropRef = useRef(null)
  const btnRef  = useRef(null)

  // Check backend health on mount
  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/health`)
      .then(r => r.json())
      .then(d => setBackendStatus(d.status === 'ok' ? 'live' : 'error'))
      .catch(() => setBackendStatus('manual'))
  }, [])

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e) {
      if (
        dropRef.current &&
        !dropRef.current.contains(e.target) &&
        btnRef.current &&
        !btnRef.current.contains(e.target)
      ) {
        setDropOpen(false)
      }
    }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  function handleStartClick() {
    setDropOpen(false)
    onStartScenario()
  }

  const isLive = backendStatus === 'live'

  return (
    <nav className="nav">
      {/* Logo */}
      <div className="logo">
        <div className="logo-icon">⬡</div>
        ChainGuard<span style={{ color: '#00d4ff' }}>AI</span>
      </div>

      {/* Center alert */}
      <div className="nav-alert">
        <div className="dot" />
        THREAT LEVEL: CRITICAL — P0 INCIDENT ACTIVE
      </div>

      {/* Right controls */}
      <div className="nav-r">
        <div className="pill">SC-2024-8891</div>
        <div className="pill" style={{ color: '#ffb340', borderColor: '#2a3820' }}>48h WINDOW</div>

        {/* Backend status badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '3px 8px',
          borderRadius: '4px',
          border: `1px solid ${isLive ? 'rgba(0,230,118,0.25)' : 'rgba(255,179,64,0.25)'}`,
          background: isLive ? 'rgba(0,230,118,0.08)' : 'rgba(255,179,64,0.08)',
        }}>
          <span style={{
            fontSize: '9px',
            fontFamily: "'JetBrains Mono', monospace",
            color: isLive ? '#00e676' : '#ffb340',
            letterSpacing: '0.05em',
          }}>
            {backendStatus === 'checking' ? '○ CONNECTING' : isLive ? '● LIVE' : '● MANUAL'}
          </span>
        </div>

        <button
          className="nbtn"
          ref={btnRef}
          onClick={() => setDropOpen(v => !v)}
        >
          ⚙ DEMO CTRL
        </button>
        <button className="nbtn danger" onClick={onReset}>↺ RESET</button>
      </div>

      {/* Demo dropdown */}
      <div className={`drop${dropOpen ? ' open' : ''}`} ref={dropRef}>
        <div className="drop-title">Demo Controller</div>

        {/* Mode indicator inside dropdown */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 8px',
          marginBottom: '8px',
          borderRadius: '4px',
          background: isLive ? 'rgba(0,230,118,0.08)' : 'rgba(255,179,64,0.08)',
          border: `1px solid ${isLive ? 'rgba(0,230,118,0.2)' : 'rgba(255,179,64,0.2)'}`,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '9px',
          color: isLive ? '#00e676' : '#ffb340',
        }}>
          {isLive
            ? '● Connected to live backend'
            : '● Manual mode — no backend detected'}
        </div>

        <select
          className="dsel"
          value={scenario}
          onChange={e => onScenarioChange(e.target.value)}
        >
          <option value="port_strike">🔴 Port Strike — Long Beach</option>
          <option value="customs_delay">🟡 Customs Delay — Shanghai</option>
          <option value="supplier_breach">🟠 Supplier Bankruptcy — Taiwan</option>
        </select>
        <button className="dbtn" onClick={handleStartClick}>▶ Start Scenario</button>
        <button className="dbtn2" onClick={onManualScript}>📜 Manual Mode Script</button>
      </div>
    </nav>
  )
}
