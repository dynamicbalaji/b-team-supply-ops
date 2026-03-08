import { SCENARIOS } from '../constants/scenarios'

export default function CrisisBanner({ scenario, tickerValue }) {
  const s = SCENARIOS[scenario] || SCENARIOS.port_strike
  const formatted = '$' + (tickerValue || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')

  return (
    <div className="crisis">
      <div style={{ display:'flex', alignItems:'center', minWidth:0, overflow:'hidden' }}>
        <span className="cbadge">CRITICAL</span>
        <span className="ctxt">
          <b>{s.title}</b> {s.crisis}
        </span>
      </div>
      <div className="ticker-wrap">
        <div className="ticker-lbl">Cost accumulating</div>
        <div className="ticker-val">{formatted}</div>
        <div className="ticker-sub">Traditional: {s.traditional}</div>
      </div>
    </div>
  )
}
