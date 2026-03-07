import { useState } from 'react'

export default function DecisionTab() {
  const [pen, setPen] = useState(2000)
  const [dl, setDl] = useState(48)
  const [bud, setBud] = useState(500)

  const savings = Math.round(220 * (pen / 2000) * (bud / 500))
  const wiResult = savings > 150
    ? `→ Hybrid saves $${savings}K · Optimal within all constraints`
    : `→ Budget too tight for hybrid — consider Air at $${Math.round(500 * (pen / 2000))}K`

  return (
    <div className="dpan">
      {/* What-If Editor */}
      <div className="wicard">
        <div className="sec-hd">
          <div className="sec-ttl">⚡ What-If Editor</div>
          <span className="bdg born">LIVE RECALC</span>
        </div>

        <div className="wirow">
          <span className="wilbl">Contract Penalty</span>
          <div className="wi-r">
            <input
              type="range"
              min="500"
              max="5000"
              value={pen}
              onChange={e => setPen(+e.target.value)}
            />
            <span className="wiv">${(pen / 1000).toFixed(1)}M</span>
          </div>
        </div>

        <div className="wirow">
          <span className="wilbl">Deadline Window</span>
          <div className="wi-r">
            <input
              type="range"
              min="12"
              max="96"
              value={dl}
              onChange={e => setDl(+e.target.value)}
            />
            <span className="wiv">{dl}h</span>
          </div>
        </div>

        <div className="wirow">
          <span className="wilbl">Budget Cap</span>
          <div className="wi-r">
            <input
              type="range"
              min="100"
              max="800"
              value={bud}
              onChange={e => setBud(+e.target.value)}
            />
            <span className="wiv">${bud}K</span>
          </div>
        </div>

        <div className="wires">{wiResult}</div>
      </div>

      {/* Decision Matrix */}
      <div className="sec-hd">
        <div className="sec-ttl">Decision Matrix</div>
        <span className="bdg brec">✦ HYBRID OPTIMAL</span>
      </div>

      <table className="mtbl">
        <thead>
          <tr>
            <th>Option</th>
            <th>Cost</th>
            <th>Time</th>
            <th>Risk</th>
            <th>ESG</th>
            <th>Customer</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span className="oname">Air Freight</span></td>
            <td style={{ color: '#ff3b5c' }}>$500K</td>
            <td>24h</td>
            <td>
              <div className="rbar">
                <div className="rf rlo" style={{ width: '18px' }} />
                2/10
              </div>
            </td>
            <td>🔴</td>
            <td><span className="bdg bgrn">None</span></td>
          </tr>
          <tr>
            <td><span className="oname">Spot Buy</span></td>
            <td style={{ color: '#ffb340' }}>$380K</td>
            <td>12h</td>
            <td>
              <div className="rbar">
                <div className="rf rhi" style={{ width: '62px' }} />
                7/10
              </div>
            </td>
            <td>🟡</td>
            <td><span className="bdg born">20% short</span></td>
          </tr>
          <tr className="rec">
            <td><span className="oname" style={{ color: '#00e676' }}>✦ Hybrid</span></td>
            <td style={{ color: '#00e676' }}>$280K</td>
            <td>36h</td>
            <td>
              <div className="rbar">
                <div className="rf rmd" style={{ width: '36px' }} />
                4/10
              </div>
            </td>
            <td>🟡</td>
            <td><span className="bdg born">Minor</span></td>
          </tr>
        </tbody>
      </table>

      {/* Monte Carlo card */}
      <div className="mccard">
        <div className="sec-hd" style={{ marginBottom: '4px' }}>
          <div className="sec-ttl">Monte Carlo Simulation</div>
          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: '#00e676' }}>
            100 iters · 94% CI
          </span>
        </div>
        <div className="mcstats">
          <div>
            <div className="mcsl">Mean</div>
            <div className="mcsv" style={{ color: '#00d4ff' }}>$280K</div>
          </div>
          <div>
            <div className="mcsl">P10</div>
            <div className="mcsv" style={{ color: '#00e676' }}>$241K</div>
          </div>
          <div>
            <div className="mcsl">P90</div>
            <div className="mcsv" style={{ color: '#ffb340' }}>$318K</div>
          </div>
          <div>
            <div className="mcsl">Saved vs Air</div>
            <div className="mcsv" style={{ color: '#00e676' }}>$220K</div>
          </div>
        </div>
        {/* Chart will be built dynamically in Phase 5 */}
        <div className="chart-area" id="mcChart">
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: '9px',
            color: '#3d5a72',
          }}>
            Run a scenario to generate simulation data
          </div>
        </div>
      </div>
    </div>
  )
}
