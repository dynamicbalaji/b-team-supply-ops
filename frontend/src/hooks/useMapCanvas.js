import { useEffect, useRef } from 'react'

// Node positions as fraction of canvas size
const N = {
  shanghai:  { x: .78, y: .27, label: 'Shanghai',   icon: '📦', col: '#7aa0be' },
  longbeach: { x: .20, y: .46, label: 'Long Beach',  icon: '🔴', col: '#ff3b5c' },
  lax:       { x: .19, y: .49, label: 'LAX',         icon: '✈',  col: '#00d4ff' },
  dallas:    { x: .29, y: .50, label: 'Dallas',      icon: '🏢', col: '#ffb340' },
  austin:    { x: .31, y: .53, label: 'Austin TX',   icon: '🏭', col: '#00e676' },
}

// Route definitions — state drives color
const ROUTES = [
  { a: 'shanghai',  b: 'longbeach', state: 'blocked',  dash: [6, 4] },
  { a: 'longbeach', b: 'lax',       state: 'active',   dash: [6, 4] },
  { a: 'lax',       b: 'austin',    state: 'active',   dash: [6, 4] },
  { a: 'longbeach', b: 'dallas',    state: 'proposed', dash: [4, 7] },
  { a: 'dallas',    b: 'austin',    state: 'proposed', dash: [4, 7] },
]

// Continent polygon coordinates [x_fraction, y_fraction]
const LAND = [
  // North America
  [[.06,.12],[.22,.10],[.32,.15],[.34,.22],[.28,.30],[.21,.38],[.18,.45],[.14,.56],[.10,.62],[.06,.60],[.03,.50],[.03,.34],[.06,.22]],
  // Central / South America
  [[.18,.55],[.24,.52],[.26,.60],[.24,.72],[.20,.78],[.16,.76],[.15,.67],[.17,.58]],
  // Europe
  [[.46,.12],[.54,.10],[.57,.16],[.56,.21],[.51,.23],[.47,.21],[.45,.15]],
  // Africa
  [[.46,.22],[.55,.20],[.58,.28],[.57,.42],[.53,.52],[.49,.53],[.46,.48],[.45,.34]],
  // Asia
  [[.54,.09],[.74,.08],[.84,.14],[.86,.22],[.82,.29],[.74,.31],[.65,.30],[.58,.26],[.54,.19]],
  // Australia
  [[.74,.51],[.83,.50],[.86,.58],[.84,.65],[.78,.66],[.73,.60],[.72,.54]],
]

// Convert fraction coords to canvas pixels
function px(canvas, key) {
  return { x: N[key].x * canvas.width, y: N[key].y * canvas.height }
}

// Bezier control point — arch ocean routes, flatten land
function cp(canvas, a, b) {
  const dist = Math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2)
  const curve = dist > 180 ? -0.22 : -0.04
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 + curve * canvas.height }
}

// Quadratic bezier interpolation
function bezPt(p0, p1, c, t) {
  return {
    x: (1 - t) ** 2 * p0.x + 2 * (1 - t) * t * c.x + t ** 2 * p1.x,
    y: (1 - t) ** 2 * p0.y + 2 * (1 - t) * t * c.y + t ** 2 * p1.y,
  }
}

export function useMapCanvas(canvasRef, { truckPhase, onTruckPhaseChange, isActive }) {
  // Refs hold animation state — never cause re-renders
  const rafRef        = useRef(null)
  const dashOffRef    = useRef(0)
  const truckTRef     = useRef(0)
  const truckPhaseRef = useRef(truckPhase)

  // Keep truckPhaseRef in sync when prop changes
  useEffect(() => {
    truckPhaseRef.current = truckPhase
    // Reset truckT when phase transitions to flying or driving
    if (truckPhase === 'flying' || truckPhase === 'driving') {
      truckTRef.current = 0
    }
  }, [truckPhase])

  // Resize canvas — runs on mount, window resize, and tab activation
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    function resize() {
      const parent = canvas.parentElement
      if (!parent) return
      canvas.width  = parent.clientWidth
      canvas.height = parent.clientHeight
    }
    resize()
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [canvasRef, isActive]) // isActive forces re-run when tab switches to map

  // Main animation loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    function drawBackground() {
      const g = ctx.createRadialGradient(
        canvas.width * 0.25, canvas.height * 0.5, 0,
        canvas.width * 0.25, canvas.height * 0.5, canvas.width * 0.7
      )
      g.addColorStop(0, 'rgba(0,40,70,.4)')
      g.addColorStop(1, 'rgba(4,8,16,1)')
      ctx.fillStyle = g
      ctx.fillRect(0, 0, canvas.width, canvas.height)
    }

    function drawGrid() {
      ctx.strokeStyle = 'rgba(0,212,255,.03)'
      ctx.lineWidth = 0.5
      const cols = 9, rows = 6
      for (let i = 0; i <= cols; i++) {
        const x = (canvas.width / cols) * i
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke()
      }
      for (let i = 0; i <= rows; i++) {
        const y = (canvas.height / rows) * i
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke()
      }
    }

    function drawLand() {
      ctx.fillStyle   = 'rgba(0,212,255,.038)'
      ctx.strokeStyle = 'rgba(0,212,255,.10)'
      ctx.lineWidth   = 0.8
      LAND.forEach(pts => {
        ctx.beginPath()
        ctx.moveTo(pts[0][0] * canvas.width, pts[0][1] * canvas.height)
        for (let i = 1; i < pts.length; i++) {
          ctx.lineTo(pts[i][0] * canvas.width, pts[i][1] * canvas.height)
        }
        ctx.closePath()
        ctx.fill()
        ctx.stroke()
      })
    }

    function drawRoutes() {
      dashOffRef.current = (dashOffRef.current + 0.35) % 22
      ROUTES.forEach(r => {
        const a = px(canvas, r.a)
        const b = px(canvas, r.b)
        const c = cp(canvas, a, b)
        ctx.beginPath()
        ctx.setLineDash(r.dash)
        ctx.lineDashOffset = -dashOffRef.current
        ctx.lineWidth = 1.6
        if      (r.state === 'blocked')  ctx.strokeStyle = 'rgba(255,59,92,.58)'
        else if (r.state === 'active')   ctx.strokeStyle = 'rgba(0,212,255,.62)'
        else if (r.state === 'proposed') ctx.strokeStyle = 'rgba(255,179,64,.38)'
        ctx.moveTo(a.x, a.y)
        ctx.quadraticCurveTo(c.x, c.y, b.x, b.y)
        ctx.stroke()
        ctx.setLineDash([])
      })
    }

    function drawNodes() {
      const t = Date.now() / 500
      Object.keys(N).forEach(k => {
        const n = N[k]
        const p = px(canvas, k)
        const pulse   = Math.sin(t + (k.length * 0.8)) * 0.5 + 0.5
        const isBlock = k === 'longbeach'
        const isDest  = k === 'austin'

        // Glow ring for blocked / destination nodes
        if (isBlock || isDest) {
          ctx.beginPath()
          ctx.arc(p.x, p.y, 10 + pulse * 5, 0, Math.PI * 2)
          ctx.fillStyle = isBlock
            ? `rgba(255,59,92,${pulse * 0.12})`
            : `rgba(0,230,118,${pulse * 0.10})`
          ctx.fill()
        }

        // Node dot
        ctx.beginPath()
        ctx.arc(p.x, p.y, 5, 0, Math.PI * 2)
        ctx.fillStyle = isBlock
          ? 'rgba(255,59,92,.3)'
          : isDest
            ? 'rgba(0,230,118,.25)'
            : 'rgba(0,212,255,.18)'
        ctx.fill()
        ctx.strokeStyle = n.col
        ctx.lineWidth   = 2
        ctx.stroke()

        // Label box
        const lbl = n.icon + ' ' + n.label
        ctx.font = '10px "JetBrains Mono",monospace'
        const tw = ctx.measureText(lbl).width
        const lx = p.x - tw / 2 - 4
        const ly = p.y - 20
        ctx.fillStyle = 'rgba(4,8,16,.82)'
        ctx.beginPath()
        if (ctx.roundRect) ctx.roundRect(lx, ly, tw + 8, 14, 3)
        else ctx.rect(lx, ly, tw + 8, 14)
        ctx.fill()
        ctx.strokeStyle = n.col
        ctx.lineWidth   = 0.6
        ctx.stroke()
        ctx.fillStyle = n.col
        ctx.fillText(lbl, p.x - tw / 2, ly + 10)
      })
    }

    function drawTruck() {
      const now   = Date.now()
      const phase = truckPhaseRef.current

      if (phase === 'blocked') {
        const p      = px(canvas, 'longbeach')
        const wobble = Math.sin(now / 900) * 3
        ctx.font = '13px serif'
        ctx.fillText('🚛', p.x + 8 + wobble, p.y + 4)
        ctx.font      = '8px "JetBrains Mono",monospace'
        ctx.fillStyle = 'rgba(255,59,92,.9)'
        ctx.fillText('HELD', p.x + 6, p.y - 7)

      } else if (phase === 'flying') {
        truckTRef.current = Math.min(1, truckTRef.current + 0.0025)
        const a = px(canvas, 'longbeach')
        const b = px(canvas, 'lax')
        const c = cp(canvas, a, b)
        const p = bezPt(a, b, c, truckTRef.current)
        ctx.beginPath(); ctx.arc(p.x, p.y, 11, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(0,212,255,.1)'; ctx.fill()
        ctx.font = '14px serif'
        ctx.fillText('🛫', p.x - 8, p.y + 6)
        if (truckTRef.current >= 1) {
          onTruckPhaseChange('driving')
        }

      } else if (phase === 'driving') {
        truckTRef.current = Math.min(1, truckTRef.current + 0.002)
        const a = px(canvas, 'lax')
        const b = px(canvas, 'austin')
        const c = cp(canvas, a, b)
        const p = bezPt(a, b, c, truckTRef.current)
        ctx.beginPath(); ctx.arc(p.x, p.y, 11, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(0,212,255,.1)'; ctx.fill()
        ctx.font = '14px serif'
        ctx.fillText('🚛', p.x - 8, p.y + 6)
        if (truckTRef.current >= 1) {
          onTruckPhaseChange('arrived')
        }

      } else if (phase === 'arrived') {
        const d = px(canvas, 'austin')
        ctx.font = '14px serif'
        ctx.fillText('✅', d.x - 7, d.y - 14)
        ctx.font      = '8px "JetBrains Mono",monospace'
        ctx.fillStyle = 'rgba(0,230,118,.9)'
        ctx.fillText('DELIVERED', d.x - 18, d.y - 20)
      }
    }

    function drawFrame() {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      drawBackground()
      drawGrid()
      drawLand()
      drawRoutes()
      drawNodes()
      drawTruck()
      rafRef.current = requestAnimationFrame(drawFrame)
    }

    rafRef.current = requestAnimationFrame(drawFrame)

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [canvasRef, onTruckPhaseChange]) // stable refs — only runs once

  // No return value needed — side-effect only
}
