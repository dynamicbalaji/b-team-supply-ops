import { SCENARIOS } from '../constants/scenarios'

function formatCost(raw) {
  if (raw == null) return null
  const num = typeof raw === 'number' ? raw : Number(String(raw).replace(/[$,]/g, ''))
  if (isNaN(num)) return raw
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(1)}M`
  if (num >= 1_000)     return `$${Math.round(num / 1000)}K`
  return `$${num}`
}

export default function BottomBar({
  scenario,
  onScenarioChange,
  resolutionTime,
  costSaved,
  msgCount,
}) {
  const s = SCENARIOS[scenario] || SCENARIOS.port_strike

  return (
    <div className="bbar">

      {/* ── Left: live metrics ── */}
      <div className="metrics">
        <div className="met">
          <span className="mlbl">AI Resolution</span>
          <span className="mval" style={{ color: resolutionTime ? '#39d98a' : undefined }}>
            {resolutionTime ?? '—'}
          </span>
        </div>
        <div className="met">
          <span className="mlbl">Cost Saved</span>
          <span className="mval ok">{formatCost(costSaved) ?? '—'}</span>
        </div>
        <div className="met">
          <span className="mlbl">Traditional</span>
          <span className="mval red">~{s.tradTime}</span>
        </div>
        <div className="met">
          <span className="mlbl">A2A Messages</span>
          <span className="mval">{msgCount ?? 0}</span>
        </div>
      </div>

      {/* ── Right: scenario selector ── */}
      <div style={{ display:'flex', alignItems:'center', gap:'7px' }}>
        <span style={{ fontSize:'9px', color:'#3d5a72', fontFamily:"'JetBrains Mono',monospace" }}>
          SCENARIO
        </span>
        <select
          className="bsel"
          value={scenario}
          onChange={e => onScenarioChange(e.target.value)}
        >
          <option value="port_strike">🔴 Port Strike (Long Beach)</option>
          <option value="customs_delay">🟡 Customs Delay (Shanghai)</option>
          <option value="supplier_breach">🟠 Supplier Bankruptcy</option>
        </select>
      </div>

    </div>
  )
}
