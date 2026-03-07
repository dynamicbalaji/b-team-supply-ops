import { useState, useEffect, useRef } from 'react'

export default function Nav({ scenario, onScenarioChange, onStartScenario, onReset, onManualScript }) {
  const [dropOpen, setDropOpen] = useState(false)
  const dropRef = useRef(null)
  const btnRef = useRef(null)

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
