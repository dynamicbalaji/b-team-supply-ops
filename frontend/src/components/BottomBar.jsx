import { useState } from 'react'

export default function BottomBar({ scenario, onScenarioChange }) {
  const [shipments, setShipments] = useState(200)
  const annualSavings = ((220 * shipments) / 1000).toFixed(1)

  return (
    <div className="bbar">
      {/* Left metrics */}
      <div className="metrics">
        <div className="met">
          <span className="mlbl">Resolution</span>
          <span className="mval">—</span>
        </div>
        <div className="met">
          <span className="mlbl">Cost Saved</span>
          <span className="mval ok">—</span>
        </div>
        <div className="met">
          <span className="mlbl">Traditional</span>
          <span className="mval red">72 hrs</span>
        </div>
        <div className="met">
          <span className="mlbl">Messages</span>
          <span className="mval">0</span>
        </div>
      </div>

      {/* Center ROI slider */}
      <div className="roi-row">
        <span className="roi-lbl">Shipments/yr:</span>
        <input
          type="range"
          min="50"
          max="500"
          value={shipments}
          onChange={e => setShipments(+e.target.value)}
        />
        <span
          className="roi-lbl"
          style={{
            minWidth: '28px',
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: '11px',
            color: '#ddeeff',
          }}
        >
          {shipments}
        </span>
        <span className="roi-lbl">→ Annual savings:</span>
        <span className="roi-val">${annualSavings}M/yr</span>
      </div>

      {/* Right scenario selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
        <span
          style={{
            fontSize: '9px',
            color: '#3d5a72',
            fontFamily: "'JetBrains Mono',monospace",
          }}
        >
          SCENARIO
        </span>
        <select
          className="bsel"
          value={scenario}
          onChange={e => onScenarioChange(e.target.value)}
        >
          <option value="port_strike">🔴 Port Strike (Long Beach)</option>
          <option value="customs_delay">🟡 Customs Delay (China)</option>
          <option value="supplier_breach">🟠 Supplier Bankruptcy</option>
        </select>
      </div>
    </div>
  )
}
