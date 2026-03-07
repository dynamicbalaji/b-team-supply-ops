import { useState, useRef, useEffect, useCallback } from 'react'

const NEW_GREEN = '#39d98a'

function drawChart(el, mcDistribution) {
  if (!el || !mcDistribution) return
  el.innerHTML = ''
  const max = Math.max(...mcDistribution)
  mcDistribution.forEach((v, i) => {
    const bar       = document.createElement('div')
    bar.className   = 'cbar'
    bar.style.flex  = '1'
    bar.style.height = '0%'
    bar.style.borderRadius = '2px 2px 0 0'
    bar.style.transition   = `height 0.75s ease ${i * 0.025}s`
    if (i < 4 || i > 17) {
      bar.style.background = 'linear-gradient(180deg,rgba(255,59,92,.5),rgba(255,59,92,.1))'
    } else if (i >= 6 && i <= 14) {
      bar.style.background = 'linear-gradient(180deg,rgba(57,217,138,.7),rgba(57,217,138,.15))'
    } else {
      bar.style.background = 'linear-gradient(180deg,rgba(0,212,255,.5),rgba(0,212,255,.1))'
    }
    el.appendChild(bar)
  })
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      el.querySelectorAll('.cbar').forEach((b, i) => {
        b.style.height = `${(mcDistribution[i] / max) * 100}%`
      })
    })
  })
}

export default function DecisionTab({ mcDistribution, mcStats, isActive }) {
  const [pen, setPen]           = useState(2000)
  const [dl,  setDl ]           = useState(48)
  const [bud, setBud]           = useState(500)
  const [roiShipments]          = useState(200)

  const chartNodeRef  = useRef(null)
  const firstOpenRef  = useRef(false)   // has the tab ever been opened with data?
  const prevActiveRef = useRef(false)   // was it active last render?

  // Callback ref — draw immediately when DOM node mounts
  const chartRef = useCallback((node) => {
    chartNodeRef.current = node
    if (node && mcDistribution) drawChart(node, mcDistribution)
  }, []) // eslint-disable-line

  // Re-draw when fresh distribution data arrives
  useEffect(() => {
    if (mcDistribution && chartNodeRef.current) {
      drawChart(chartNodeRef.current, mcDistribution)
      firstOpenRef.current = true
    }
  }, [mcDistribution])

  // Re-animate chart when user first opens the tab after data already exists
  useEffect(() => {
    const justOpened = isActive && !prevActiveRef.current
    prevActiveRef.current = isActive

    if (justOpened && mcDistribution && chartNodeRef.current && !firstOpenRef.current) {
      // Small delay to let the tpane become visible before animating
      const t = setTimeout(() => {
        drawChart(chartNodeRef.current, mcDistribution)
        firstOpenRef.current = true
      }, 80)
      return () => clearTimeout(t)
    }
  }, [isActive, mcDistribution])

  const savings = Math.round(220 * (pen / 2000) * (bud / 500))
  const stats   = mcStats || { mean: 280000, p10: 241000, p90: 318000, ci: 0.94 }

  return (
    <div className="dpan">

      {/* ── What-If Editor ── */}
      <div className="wicard">
        <div className="sec-hd">
          <div className="sec-ttl">⚡ What-If Editor</div>
          <span className="bdg born">LIVE RECALC</span>
        </div>

        <div className="wirow">
          <span className="wilbl">Contract Penalty</span>
          <div className="wi-r">
            <input type="range" min="500" max="5000" value={pen}
              onChange={e => setPen(+e.target.value)} />
            <span className="wiv">${(pen / 1000).toFixed(1)}M</span>
          </div>
        </div>

        <div className="wirow">
          <span className="wilbl">Deadline Window</span>
          <div className="wi-r">
            <input type="range" min="12" max="96" value={dl}
              onChange={e => setDl(+e.target.value)} />
            <span className="wiv">{dl}h</span>
          </div>
        </div>

        <div className="wirow">
          <span className="wilbl">Budget Cap</span>
          <div className="wi-r">
            <input type="range" min="100" max="800" value={bud}
              onChange={e => setBud(+e.target.value)} />
            <span className="wiv">${bud}K</span>
          </div>
        </div>

        <div className="wires" style={{ color: savings > 150 ? NEW_GREEN : '#ffb340' }}>
          → Hybrid saves ${savings}K · At {roiShipments} shipments/yr → ${(savings * roiShipments / 1000).toFixed(1)}M/yr saved
        </div>
      </div>

      {/* ── Decision Matrix ── */}
      <div className="sec-hd">
        <div className="sec-ttl">Decision Matrix</div>
        <span className="bdg brec">✦ HYBRID OPTIMAL</span>
      </div>

      <table className="mtbl">
        <thead>
          <tr>
            <th>Option</th><th>Cost</th><th>Time</th>
            <th>Risk</th><th>ESG</th><th>Customer</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span className="oname">Air Freight</span></td>
            <td style={{ color: '#ff3b5c' }}>$500K</td>
            <td>24h</td>
            <td><div className="rbar"><div className="rf rlo" style={{ width: '18px' }} />2/10</div></td>
            <td>🔴</td>
            <td><span className="bdg bgrn">None</span></td>
          </tr>
          <tr>
            <td><span className="oname">Spot Buy</span></td>
            <td style={{ color: '#ffb340' }}>$380K</td>
            <td>12h</td>
            <td><div className="rbar"><div className="rf rhi" style={{ width: '62px' }} />7/10</div></td>
            <td>🟡</td>
            <td><span className="bdg born">20% short</span></td>
          </tr>
          <tr className="rec">
            <td><span className="oname" style={{ color: NEW_GREEN }}>✦ Hybrid</span></td>
            <td style={{ color: NEW_GREEN }}>$280K</td>
            <td>36h</td>
            <td><div className="rbar"><div className="rf rmd" style={{ width: '36px' }} />4/10</div></td>
            <td>🟡</td>
            <td><span className="bdg born">Minor</span></td>
          </tr>
        </tbody>
      </table>

      {/* ── Monte Carlo ── */}
      <div className="mccard">
        <div className="sec-hd" style={{ marginBottom: '4px' }}>
          <div className="sec-ttl">Monte Carlo Simulation</div>
          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: NEW_GREEN }}>
            100 iters · {Math.round((stats.ci ?? 0.94) * 100)}% CI
          </span>
        </div>

        <div className="mcstats">
          <div>
            <div className="mcsl">Mean</div>
            <div className="mcsv" style={{ color: '#00d4ff' }}>${(stats.mean / 1000).toFixed(0)}K</div>
          </div>
          <div>
            <div className="mcsl">P10</div>
            <div className="mcsv" style={{ color: NEW_GREEN }}>${(stats.p10 / 1000).toFixed(0)}K</div>
          </div>
          <div>
            <div className="mcsl">P90</div>
            <div className="mcsv" style={{ color: '#ffb340' }}>${(stats.p90 / 1000).toFixed(0)}K</div>
          </div>
          <div>
            <div className="mcsl">Saved vs Air</div>
            <div className="mcsv" style={{ color: NEW_GREEN }}>$220K</div>
          </div>
        </div>

        {/* Chart — always rendered so ref is always attached */}
        <div className="chart-area" id="mcChart" style={{ position: 'relative' }}>
          {!mcDistribution && (
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: '#3d5a72',
              pointerEvents: 'none',
            }}>
              Run a scenario to generate simulation data
            </div>
          )}
          <div
            ref={chartRef}
            style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', width: '100%', height: '100%' }}
          />
        </div>
      </div>

    </div>
  )
}
