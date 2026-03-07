export default function BottomBar({
  scenario,
  onScenarioChange,
  resolutionTime,
  costSaved,
  msgCount,
}) {
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
          <span className="mval ok">{costSaved ?? '—'}</span>
        </div>
        <div className="met">
          <span className="mlbl">Traditional</span>
          <span className="mval red">~72 hrs</span>
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
          <option value="customs_delay">🟡 Customs Delay (China)</option>
          <option value="supplier_breach">🟠 Supplier Bankruptcy</option>
        </select>
      </div>

    </div>
  )
}
