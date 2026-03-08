/**
 * DecisionTab.jsx
 *
 * Decision Matrix + What-If Editor + Monte Carlo — fully scenario-reactive.
 *
 * What changed vs the hardcoded version:
 *  1. What-If sliders seed from the active scenario's real values on every new run.
 *     Slider ranges also scale with the scenario (customs_delay has a lower penalty
 *     ceiling than supplier_breach, etc.).
 *  2. Savings formula uses the actual air-vs-hybrid delta per scenario, not a
 *     hardcoded $220K port-strike figure.
 *  3. Matrix rows animate in with a staggered slide+fade whenever runId changes —
 *     same visual refresh mechanic as the MC histogram bars.
 *  4. Recommended badge fades in once options have loaded.
 *  5. MC "Saved vs Air" pulls from API, falling back to per-scenario default.
 *  6. All hardcoded port-strike numbers are gone.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { useDecisionMatrix } from '../../hooks/useDecisionMatrix'

const NEW_GREEN = '#39d98a'

// ── Per-scenario slider seeds and formula constants ───────────────────────
// pen/bud are in slider units ($K). airVsHybridSavings is also $K.
const SCENARIO_DEFAULTS = {
  port_strike:     { pen: 2000, penMin: 500,  penMax: 5000, dl: 48, dlMin: 12, dlMax: 96,  bud: 500, budMin: 100, budMax: 800,  roiShipments: 200, airVsHybridSavings: 220 },
  customs_delay:   { pen: 1500, penMin: 375,  penMax: 3750, dl: 36, dlMin: 9,  dlMax: 72,  bud: 400, budMin: 80,  budMax: 640,  roiShipments: 150, airVsHybridSavings: 140 },
  supplier_breach: { pen: 5000, penMin: 1250, penMax: 7500, dl: 72, dlMin: 18, dlMax: 144, bud: 800, budMin: 200, budMax: 1200, roiShipments: 80,  airVsHybridSavings: 170 },
}
const FALLBACK_DEF = SCENARIO_DEFAULTS.port_strike

// ── Monte Carlo histogram drawing ─────────────────────────────────────────

function drawChart(el, distribution) {
  if (!el || !distribution || distribution.length === 0) return
  el.innerHTML = ''
  const max   = Math.max(...distribution)
  const total = distribution.length
  const lo    = Math.floor(total * 0.2)
  const hi    = Math.floor(total * 0.8)
  distribution.forEach((v, i) => {
    const bar = document.createElement('div')
    bar.className      = 'cbar'
    bar.style.flex     = '1'
    bar.style.height   = '0%'
    bar.style.borderRadius = '2px 2px 0 0'
    bar.style.transition   = `height 0.75s ease ${i * 0.025}s`
    if (i < lo || i > hi) {
      bar.style.background = 'linear-gradient(180deg,rgba(255,59,92,.5),rgba(255,59,92,.1))'
    } else if (i >= Math.floor(total * 0.3) && i <= Math.floor(total * 0.7)) {
      bar.style.background = 'linear-gradient(180deg,rgba(57,217,138,.7),rgba(57,217,138,.15))'
    } else {
      bar.style.background = 'linear-gradient(180deg,rgba(0,212,255,.5),rgba(0,212,255,.1))'
    }
    el.appendChild(bar)
  })
  requestAnimationFrame(() => requestAnimationFrame(() => {
    el.querySelectorAll('.cbar').forEach((b, i) => {
      b.style.height = `${(distribution[i] / max) * 100}%`
    })
  }))
}

// ── ESG dot ───────────────────────────────────────────────────────────────
const ESG_DOT = { low: '🟢', medium: '🟡', high: '🔴' }

// ── Skeleton loading row ──────────────────────────────────────────────────
function SkeletonRow({ opacity = 1 }) {
  return (
    <tr style={{ opacity }}>
      {[80, 55, 40, 65, 30, 50].map((w, i) => (
        <td key={i}>
          <div style={{
            height: '9px', borderRadius: '3px', width: `${w}%`,
            background: 'linear-gradient(90deg,#0d2233 25%,#1a3a52 50%,#0d2233 75%)',
            backgroundSize: '200% 100%', animation: 'shimmer 1.5s infinite',
          }} />
        </td>
      ))}
    </tr>
  )
}

// ── Matrix row with staggered entrance animation ──────────────────────────
// animKey (= runId) causes the animation to re-trigger on every new run.
function MatrixRow({ opt, idx, recommended, animKey }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    setVisible(false)
    const t = setTimeout(() => setVisible(true), 60 + idx * 130)
    return () => clearTimeout(t)
  }, [animKey, idx])

  const name    = opt.name || opt.option || opt.label || ''
  const cost    = opt.cost ?? opt.cost_usd ?? 0
  const costFmt = cost >= 1_000_000 ? `$${(cost / 1_000_000).toFixed(1)}M`
                : cost >= 1_000     ? `$${Math.round(cost / 1_000)}K`
                : `$${cost}`
  const time    = opt.time || opt.delivery_time || '—'
  const risk    = typeof opt.risk === 'number' ? opt.risk : (opt.risk_score ?? 5)
  const esg     = opt.esg || (risk <= 3 ? 'low' : risk <= 6 ? 'medium' : 'high')
  const cust    = opt.customer || opt.customer_impact || '—'
  const isRec   = opt.recommended === true
               || name.toLowerCase().includes((recommended || 'hybrid').toLowerCase())
  const costClr = cost > 400_000 ? '#ff3b5c' : cost > 300_000 ? '#ffb340' : NEW_GREEN
  const riskW   = `${Math.round((risk / 10) * 70)}px`
  const riskCls = risk <= 3 ? 'rlo' : risk <= 6 ? 'rmd' : 'rhi'

  return (
    <tr
      className={isRec ? 'rec' : ''}
      style={{
        opacity:    visible ? 1 : 0,
        transform:  visible ? 'translateX(0)' : 'translateX(-10px)',
        transition: `opacity 0.4s ease ${idx * 0.12}s, transform 0.4s ease ${idx * 0.12}s`,
      }}
    >
      <td>
        <span className="oname" style={isRec ? { color: NEW_GREEN } : {}}>
          {isRec ? '✦ ' : ''}{name}
        </span>
      </td>
      <td style={{ color: costClr }}>{costFmt}</td>
      <td>{time}</td>
      <td>
        <div className="rbar">
          <div className={`rf ${riskCls}`} style={{ width: riskW }} />
          {risk}/10
        </div>
      </td>
      <td>{ESG_DOT[esg] || '🟡'}</td>
      <td><span className={`bdg ${isRec ? 'born' : 'bgrn'}`}>{cust}</span></td>
    </tr>
  )
}

// ─────────────────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────────────────

export default function DecisionTab({
  runId,
  scenario,            // "port_strike" | "customs_delay" | "supplier_breach"
  mcDistribution,      // from SSE tool event — takes priority for histogram
  mcStats: sseMcStats, // from SSE tool event — takes priority for numbers
  isActive,
  approvalData,
  isRunning,
}) {
  const everStarted = isRunning || !!mcDistribution || !!approvalData || !!runId
  const scDef = SCENARIO_DEFAULTS[scenario] || FALLBACK_DEF

  // ── What-If state — re-seeded on scenario change ─────────────────────
  const [pen, setPen] = useState(scDef.pen)
  const [dl,  setDl]  = useState(scDef.dl)
  const [bud, setBud] = useState(scDef.bud)

  const prevScenarioRef = useRef(scenario)
  useEffect(() => {
    if (scenario !== prevScenarioRef.current) {
      prevScenarioRef.current = scenario
      const d = SCENARIO_DEFAULTS[scenario] || FALLBACK_DEF
      setPen(d.pen); setDl(d.dl); setBud(d.bud)
    }
  }, [scenario])

  // ── API data ──────────────────────────────────────────────────────────
  const { options, mcStats: apiMcStats, recommended, loading } =
    useDecisionMatrix(runId, isRunning, approvalData)

  // SSE stats always win while the run is live; API fills gaps
  const stats = {
    mean:         sseMcStats?.mean ?? apiMcStats.mean ?? 280_000,
    p10:          sseMcStats?.p10  ?? apiMcStats.p10  ?? 241_000,
    p90:          sseMcStats?.p90  ?? apiMcStats.p90  ?? 318_000,
    ci:           sseMcStats?.ci   ?? apiMcStats.ci   ?? 0.94,
    saved_vs_air: apiMcStats.saved_vs_air ?? (scDef.airVsHybridSavings * 1_000),
  }

  // Histogram — SSE first, then API, then null (shows placeholder)
  const chartDistribution = mcDistribution?.length > 0
    ? mcDistribution
    : (apiMcStats.distribution?.length > 0 ? apiMcStats.distribution : null)

  // ── What-If savings formula — scenario-aware ──────────────────────────
  const savings   = Math.round(scDef.airVsHybridSavings * (pen / scDef.pen) * (bud / scDef.bud))
  const roiAnnual = (savings * scDef.roiShipments / 1_000).toFixed(1)
  const savingsGood = savings > scDef.airVsHybridSavings * 0.7

  // ── Chart refs ────────────────────────────────────────────────────────
  const chartNodeRef   = useRef(null)
  const firstOpenRef   = useRef(false)
  const prevActiveRef  = useRef(false)
  const prevRunRef     = useRef(runId)

  // Reset chart animation flag on new run
  useEffect(() => {
    if (runId !== prevRunRef.current) {
      prevRunRef.current   = runId
      firstOpenRef.current = false
    }
  }, [runId])

  const chartRef = useCallback((node) => {
    chartNodeRef.current = node
    if (node && chartDistribution) drawChart(node, chartDistribution)
  }, []) // eslint-disable-line

  useEffect(() => {
    if (chartDistribution && chartNodeRef.current) {
      drawChart(chartNodeRef.current, chartDistribution)
      firstOpenRef.current = true
    }
  }, [chartDistribution])

  useEffect(() => {
    const justOpened = isActive && !prevActiveRef.current
    prevActiveRef.current = isActive
    if (justOpened && chartDistribution && chartNodeRef.current && !firstOpenRef.current) {
      const t = setTimeout(() => {
        drawChart(chartNodeRef.current, chartDistribution)
        firstOpenRef.current = true
      }, 80)
      return () => clearTimeout(t)
    }
  }, [isActive, chartDistribution])

  // ── Empty state ───────────────────────────────────────────────────────
  if (!everStarted) {
    return (
      <div style={{
        display:'flex', flexDirection:'column', alignItems:'center',
        justifyContent:'center', height:'100%', gap:'12px', opacity:.35,
      }}>
        <img src="/shield-icon.png" alt="" className="empty-shield-icon" />
        <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'11px', color:'#3d5a72' }}>
          Run a scenario to populate
        </div>
        <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'11px', color:'#3d5a72' }}>
          the Decision Matrix
        </div>
      </div>
    )
  }

  const recLabel = (recommended || 'HYBRID').toUpperCase()

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
            <input type="range"
              min={scDef.penMin} max={scDef.penMax} step={100} value={pen}
              onChange={e => setPen(+e.target.value)} />
            <span className="wiv">${(pen / 1000).toFixed(1)}M</span>
          </div>
        </div>

        <div className="wirow">
          <span className="wilbl">Deadline Window</span>
          <div className="wi-r">
            <input type="range"
              min={scDef.dlMin} max={scDef.dlMax} step={1} value={dl}
              onChange={e => setDl(+e.target.value)} />
            <span className="wiv">{dl}h</span>
          </div>
        </div>

        <div className="wirow">
          <span className="wilbl">Budget Cap</span>
          <div className="wi-r">
            <input type="range"
              min={scDef.budMin} max={scDef.budMax} step={10} value={bud}
              onChange={e => setBud(+e.target.value)} />
            <span className="wiv">${bud}K</span>
          </div>
        </div>

        <div className="wires" style={{ color: savingsGood ? NEW_GREEN : '#ffb340' }}>
          → Hybrid saves ${savings}K · At {scDef.roiShipments} shipments/yr → ${roiAnnual}M/yr saved
        </div>
      </div>

      {/* ── Decision Matrix ── */}
      <div className="sec-hd">
        <div className="sec-ttl">Decision Matrix</div>
        <span className="bdg brec" style={{
          transition: 'opacity 0.5s ease',
          opacity: options.length > 0 ? 1 : 0.35,
        }}>
          ✦ {recLabel} OPTIMAL
        </span>
      </div>

      <table className="mtbl">
        <thead>
          <tr><th>Option</th><th>Cost</th><th>Time</th><th>Risk</th><th>ESG</th><th>Customer</th></tr>
        </thead>
        <tbody>
          {loading && options.length === 0 && (
            <>
              <SkeletonRow opacity={1} />
              <SkeletonRow opacity={0.55} />
              <SkeletonRow opacity={0.25} />
            </>
          )}

          {options.map((opt, i) => (
            <MatrixRow
              key={`${runId}-${i}`}
              opt={opt} idx={i}
              recommended={recommended}
              animKey={runId}
            />
          ))}

          {options.length === 0 && !loading && (
            <tr>
              <td colSpan={6} style={{
                textAlign:'center', fontFamily:"'JetBrains Mono',monospace",
                fontSize:'10px', color:'#3d5a72', padding:'14px 0',
              }}>
                Agents evaluating options…
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {/* ── Monte Carlo ── */}
      <div className="mccard">
        <div className="sec-hd" style={{ marginBottom:'4px' }}>
          <div className="sec-ttl">Monte Carlo Simulation</div>
          <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:NEW_GREEN }}>
            100 iters · {Math.round((stats.ci ?? 0.94) * 100)}% CI
          </span>
        </div>

        <div className="mcstats">
          <div>
            <div className="mcsl">Mean</div>
            <div className="mcsv" style={{ color:'#00d4ff' }}>${(stats.mean / 1000).toFixed(0)}K</div>
          </div>
          <div>
            <div className="mcsl">P10</div>
            <div className="mcsv" style={{ color:NEW_GREEN }}>${(stats.p10 / 1000).toFixed(0)}K</div>
          </div>
          <div>
            <div className="mcsl">P90</div>
            <div className="mcsv" style={{ color:'#ffb340' }}>${(stats.p90 / 1000).toFixed(0)}K</div>
          </div>
          <div>
            <div className="mcsl">Saved vs Air</div>
            <div className="mcsv" style={{ color:NEW_GREEN }}>${Math.round(stats.saved_vs_air / 1000)}K</div>
          </div>
        </div>

        <div className="chart-area" id="mcChart" style={{ position:'relative' }}>
          {!chartDistribution && (
            <div style={{
              position:'absolute', inset:0, display:'flex', alignItems:'center',
              justifyContent:'center', fontFamily:"'JetBrains Mono',monospace",
              fontSize:'9px', color:'#3d5a72', pointerEvents:'none',
            }}>
              {loading ? 'Loading simulation data…' : 'Run a scenario to generate simulation data'}
            </div>
          )}
          <div
            ref={chartRef}
            style={{ display:'flex', alignItems:'flex-end', gap:'2px', width:'100%', height:'100%' }}
          />
        </div>
      </div>

    </div>
  )
}
