import { useEffect, useRef } from 'react'

// ─── Nodes ────────────────────────────────────────────────────────────────────
const NODES = {
  // ── Port Strike nodes ─────────────────────────────────────────────────────
  shanghai:     { lat: 31.23,  lng: 121.47,  label: 'Shanghai Port',    icon: '📦', color: '#7aa0be' },
  longbeach:    { lat: 33.75,  lng: -118.19, label: 'Long Beach Port',  icon: '🔴', color: '#ff3b5c' },
  lax:          { lat: 33.94,  lng: -118.41, label: 'LAX Airport',      icon: '✈',  color: '#00d4ff' },
  dallas:       { lat: 32.78,  lng: -96.80,  label: 'Dallas DC',        icon: '🏢', color: '#ffb340' },
  apple_austin: { lat: 30.27,  lng: -97.74,  label: 'Apple Austin',     icon: '🏭', color: '#39d98a' },
  // ── Customs Delay nodes ───────────────────────────────────────────────────
  // Origin is Shanghai; shipment clears ocean and gets held at LAX CBP
  sh_customs:   { lat: 31.23,  lng: 121.65,  label: 'Shanghai Customs ⚠', icon: '🔴', color: '#ff3b5c' },
  chicago:      { lat: 41.88,  lng: -87.63,  label: 'Chicago Plant',    icon: '🏭', color: '#39d98a' },
  // ── Supplier Breach nodes ─────────────────────────────────────────────────
  taipei:       { lat: 25.03,  lng: 121.56,  label: 'ChipTech Taiwan',  icon: '🔴', color: '#ff3b5c' },
  samsung_seoul:{ lat: 37.56,  lng: 126.98,  label: 'Samsung Seoul',    icon: '🏭', color: '#39d98a' },
  tsmc_arizona: { lat: 33.42,  lng: -111.93, label: 'TSMC Arizona',     icon: '🏢', color: '#ffb340' },
  nvidia_sc:    { lat: 37.36,  lng: -121.92, label: 'NVIDIA San Jose',  icon: '🏢', color: '#7aa0be' },
}

// ─── Scenarios ────────────────────────────────────────────────────────────────
const SCENARIOS = {
  port_strike: {
    // Shanghai → Long Beach (BLOCKED by strike) → reroute: air to LAX → truck to Apple Austin
    bounds: [[10, 110], [55, -75]],
    activeNodes: ['shanghai', 'longbeach', 'lax', 'dallas', 'apple_austin'],
    blockedNode: 'longbeach',
    blockedLabel: '⚠ ILWU STRIKE · PORT BLOCKED',
    badgeOffset: [2.0, 2.5],
    routes: [
      // Original ocean route — blocked
      { path: ['shanghai', 'longbeach'],          state: 'blocked',  arc: true  },
      // Air reroute: Shanghai → LAX (active alternative)
      { path: ['shanghai', 'lax'],                state: 'active',   arc: true  },
      // Ground: LAX → Dallas DC → Apple Austin
      { path: ['lax', 'dallas', 'apple_austin'],  state: 'active',   arc: false },
    ],
    // Vehicle travels the active reroute path
    vehicleOcean:  ['shanghai', 'lax'],
    vehicleGround: ['lax', 'dallas', 'apple_austin'],
  },

  customs_delay: {
    // Shipment HELD at Shanghai customs/export — can't leave port
    // Resolution: expedited clearance → ocean → LAX → Chicago Plant
    bounds: [[15, 105], [55, -75]],
    activeNodes: ['sh_customs', 'lax', 'chicago'],
    blockedNode: 'sh_customs',
    blockedLabel: '⚠ CUSTOMS HOLD · SHANGHAI PORT',
    badgeOffset: [2.2, 2.5],
    routes: [
      // Blocked at source — can't depart
      { path: ['sh_customs', 'lax'],    state: 'blocked',  arc: true  },
      // Once cleared: ocean to LAX then ground to Chicago
      { path: ['sh_customs', 'lax'],    state: 'active',   arc: true  },
      { path: ['lax', 'chicago'],       state: 'proposed', arc: false },
    ],
    vehicleOcean:  ['sh_customs', 'lax'],
    vehicleGround: ['lax', 'chicago'],
  },

  supplier_breach: {
    // ChipTech Taiwan BANKRUPT → cancelled order
    // Alternative 1: Samsung Seoul → ship → TSMC Arizona → truck → NVIDIA San Jose
    // Alternative 2: TSMC Arizona (direct fab) → truck → NVIDIA San Jose
    bounds: [[15, 110], [55, -80]],
    activeNodes: ['taipei', 'samsung_seoul', 'tsmc_arizona', 'nvidia_sc'],
    blockedNode: 'taipei',
    blockedLabel: '⚠ CHIPTEC BANKRUPT · ORDER CANCELLED',
    badgeOffset: [1.8, -3.0],
    routes: [
      // Original order — cancelled/blocked
      { path: ['taipei', 'nvidia_sc'],             state: 'blocked',  arc: true  },
      // Alt 1: Samsung Seoul → ocean → TSMC Arizona
      { path: ['samsung_seoul', 'tsmc_arizona'],   state: 'active',   arc: true  },
      // Final leg: TSMC Arizona → NVIDIA San Jose
      { path: ['tsmc_arizona', 'nvidia_sc'],       state: 'active',   arc: false },
    ],
    vehicleOcean:  ['samsung_seoul', 'tsmc_arizona'],
    vehicleGround: ['tsmc_arizona', 'nvidia_sc'],
  },
}

// ─── Correct great-circle interpolation using SLERP ──────────────────────────
// This avoids the sin(PI)/sin(PI) ≈ 0/0 division bug in the old formula.
function gcPoints(nodeA, nodeB, steps = 80) {
  const toRad = d => (d * Math.PI) / 180
  const toDeg = r => (r * 180) / Math.PI

  const φ1 = toRad(nodeA.lat), λ1 = toRad(nodeA.lng)
  const φ2 = toRad(nodeB.lat), λ2 = toRad(nodeB.lng)

  // Convert to 3-D unit vectors
  const v1 = [Math.cos(φ1)*Math.cos(λ1), Math.cos(φ1)*Math.sin(λ1), Math.sin(φ1)]
  const v2 = [Math.cos(φ2)*Math.cos(λ2), Math.cos(φ2)*Math.sin(λ2), Math.sin(φ2)]

  // Angular distance
  const dot = Math.min(1, Math.max(-1, v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]))
  const omega = Math.acos(dot)

  // If points are essentially the same, return a trivial path
  if (omega < 0.0001) return [[nodeA.lat, nodeA.lng], [nodeB.lat, nodeB.lng]]

  const pts = []
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const sinO = Math.sin(omega)
    const A = Math.sin((1 - t) * omega) / sinO
    const B = Math.sin(t * omega) / sinO
    const x = A * v1[0] + B * v2[0]
    const y = A * v1[1] + B * v2[1]
    const z = A * v1[2] + B * v2[2]
    const lat = toDeg(Math.atan2(z, Math.sqrt(x*x + y*y)))
    const lng = toDeg(Math.atan2(y, x))
    if (isFinite(lat) && isFinite(lng)) pts.push([lat, lng])
  }
  return pts.length >= 2 ? pts : [[nodeA.lat, nodeA.lng], [nodeB.lat, nodeB.lng]]
}

// Simple straight line between two nodes
function straightPts(nodes) {
  return nodes.map(k => [NODES[k].lat, NODES[k].lng])
}

// Lerp along a path array at t ∈ [0,1]
function lerpPath(path, t) {
  if (!path || path.length === 0) return [0, 0]
  if (t <= 0) return path[0]
  if (t >= 1) return path[path.length - 1]
  const s = t * (path.length - 1)
  const i = Math.floor(s)
  const f = s - i
  const a = path[Math.min(i, path.length - 2)]
  const b = path[Math.min(i + 1, path.length - 1)]
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f]
}

// Build path for a route definition
function buildPath(route) {
  if (route.arc && route.path.length === 2) {
    return gcPoints(NODES[route.path[0]], NODES[route.path[1]])
  }
  return straightPts(route.path)
}

// ─── Marker HTML ──────────────────────────────────────────────────────────────
const STYLES = {
  blocked:  { color: '#ff3b5c', weight: 3,   opacity: 0.88, dash: '10 7'  },
  active:   { color: '#00d4ff', weight: 3.5, opacity: 0.92, dash: '10 5'  },
  proposed: { color: '#ffb340', weight: 2,   opacity: 0.55, dash: '6 10'  },
}

function vehicleHtml(emoji, color, badge) {
  return `<div style="display:flex;flex-direction:column;align-items:center;gap:3px;pointer-events:none;">
    <div style="width:36px;height:36px;background:${color}1a;border:2.5px solid ${color};
      border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;
      box-shadow:0 0 18px ${color}bb,0 0 5px ${color};
      animation:lf_pulse 1.1s ease-in-out infinite;">${emoji}</div>
    <div style="background:rgba(4,8,16,0.95);border:1px solid ${color};border-radius:3px;
      padding:2px 7px;font-family:'JetBrains Mono',monospace;font-size:8px;color:${color};
      white-space:nowrap;box-shadow:0 0 8px ${color}55;font-weight:700;letter-spacing:0.4px;">${badge}</div>
  </div>`
}

function arrivedHtml() {
  const c = '#39d98a'
  return `<div style="display:flex;flex-direction:column;align-items:center;gap:3px;pointer-events:none;">
    <div style="width:38px;height:38px;background:${c}18;border:2.5px solid ${c};
      border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:19px;
      box-shadow:0 0 22px ${c}99;">✅</div>
    <div style="background:rgba(4,8,16,0.95);border:1px solid ${c};border-radius:3px;
      padding:2px 7px;font-family:'JetBrains Mono',monospace;font-size:8px;color:${c};
      font-weight:700;letter-spacing:0.4px;">DELIVERED</div>
  </div>`
}

function nodeHtml(node, blocked) {
  const c = blocked ? '#ff3b5c' : node.color
  const ring = blocked
    ? `<div style="position:absolute;width:22px;height:22px;border-radius:50%;
        border:1.5px solid rgba(255,59,92,0.45);top:-5px;left:-5px;
        animation:lf_ring 1.4s ease-out infinite;"></div>` : ''
  const pulse = blocked ? 'animation:lf_pulse 0.9s ease-in-out infinite;' : ''
  return `<div style="display:flex;flex-direction:column;align-items:center;gap:4px;pointer-events:none;">
    <div style="position:relative;display:flex;align-items:center;justify-content:center;">
      ${ring}
      <div style="width:12px;height:12px;background:${c};border-radius:50%;
        border:2px solid rgba(255,255,255,0.18);
        box-shadow:0 0 16px ${c}cc,0 0 5px ${c};${pulse}"></div>
    </div>
    <div style="background:rgba(6,9,15,0.94);border:1px solid ${c}99;border-radius:4px;
      padding:2px 7px;font-family:'JetBrains Mono',monospace;font-size:9px;color:${c};
      white-space:nowrap;box-shadow:0 0 10px ${c}33;">${node.icon} ${node.label}</div>
  </div>`
}

function badgeHtml(text) {
  return `<div style="background:rgba(255,59,92,0.16);border:1.5px solid rgba(255,59,92,0.65);
    border-radius:5px;padding:4px 11px;font-family:'JetBrains Mono',monospace;
    font-size:9px;color:#ff7a8a;white-space:nowrap;
    box-shadow:0 0 16px rgba(255,59,92,0.35);font-weight:700;letter-spacing:0.5px;
    pointer-events:none;">${text}</div>`
}

// ─── Hook ─────────────────────────────────────────────────────────────────────
export function useLeafletMap(containerRef, { scenario, truckPhase, onTruckPhaseChange, isActive }) {
  // All mutable state lives in refs — never causes re-renders
  const mapRef          = useRef(null)
  const layerGroupRef   = useRef(null)
  const movingMarkerRef = useRef(null)
  const animFrameRef    = useRef(null)
  const truckTRef       = useRef(0)
  const truckPhaseRef   = useRef(truckPhase)
  const scenarioRef     = useRef(scenario)
  const readyRef        = useRef(false)
  const destroyedRef    = useRef(false)   // StrictMode: track if cleanup ran

  // ── Sync phase ref ───────────────────────────────────────────────────────
  useEffect(() => {
    truckPhaseRef.current = truckPhase
    if (truckPhase === 'flying' || truckPhase === 'driving') truckTRef.current = 0
  }, [truckPhase])

  // ── Redraw on scenario change ────────────────────────────────────────────
  useEffect(() => {
    scenarioRef.current = scenario
    if (readyRef.current && !destroyedRef.current) rebuildLayers()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario])

  // ── Resize when tab becomes active ──────────────────────────────────────
  useEffect(() => {
    if (isActive && mapRef.current) {
      setTimeout(() => {
        if (mapRef.current) {
          mapRef.current.invalidateSize()
          fitBounds()
        }
      }, 90)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive])

  // ── Init map (runs once — StrictMode-safe) ───────────────────────────────
  useEffect(() => {
    // StrictMode fix: if container already has leaflet's _leaflet_id, clear it
    if (containerRef.current) {
      delete containerRef.current._leaflet_id
    }
    destroyedRef.current = false

    const boot = () => {
      // Double-check the container hasn't been torn down already (StrictMode)
      if (!containerRef.current || destroyedRef.current) return
      // Extra guard: if Leaflet already attached to this element, bail
      if (containerRef.current._leaflet_id) return

      const Lf = window.L
      const map = Lf.map(containerRef.current, {
        center:             [32, -20],
        zoom:               3,
        zoomControl:        true,
        scrollWheelZoom:    true,
        attributionControl: false,
        inertia:            true,
      })

      Lf.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd', maxZoom: 19, detectRetina: true,
      }).addTo(map)

      mapRef.current = map
      layerGroupRef.current = Lf.layerGroup().addTo(map)
      readyRef.current = true

      rebuildLayers()
      fitBounds()
      startAnimation()
    }

    // Inject CSS once
    if (!document.getElementById('lf-css')) {
      const link = document.createElement('link')
      link.id = 'lf-css'; link.rel = 'stylesheet'
      link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css'
      document.head.appendChild(link)
    }

    // Inject animation keyframes once
    if (!document.getElementById('lf-anims')) {
      const style = document.createElement('style')
      style.id = 'lf-anims'
      style.textContent = `
        @keyframes lf_pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.3);opacity:0.6} }
        @keyframes lf_ring  { 0%{transform:scale(1);opacity:0.9} 100%{transform:scale(2.5);opacity:0} }
      `
      document.head.appendChild(style)
    }

    if (window.L) {
      boot()
    } else if (!document.getElementById('lf-js')) {
      const script = document.createElement('script')
      script.id  = 'lf-js'
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js'
      script.onload = boot
      document.head.appendChild(script)
    } else {
      // Script tag already in DOM (added by a previous mount), wait for it
      const poll = setInterval(() => {
        if (window.L) { clearInterval(poll); boot() }
      }, 50)
    }

    // Cleanup — runs on unmount AND on StrictMode's fake-unmount
    return () => {
      destroyedRef.current = true
      readyRef.current = false
      if (animFrameRef.current) { cancelAnimationFrame(animFrameRef.current); animFrameRef.current = null }
      if (movingMarkerRef.current) { movingMarkerRef.current.remove(); movingMarkerRef.current = null }
      if (mapRef.current) { mapRef.current.remove(); mapRef.current = null }
      // Clear the leaflet ID so a fresh mount can re-init the same DOM node
      if (containerRef.current) delete containerRef.current._leaflet_id
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── Build scenario layers ─────────────────────────────────────────────────
  function rebuildLayers() {
    const Lf = window.L
    if (!Lf || !mapRef.current || !layerGroupRef.current) return

    layerGroupRef.current.clearLayers()
    if (movingMarkerRef.current) {
      movingMarkerRef.current.remove()
      movingMarkerRef.current = null
    }
    truckTRef.current = 0

    const cfg = SCENARIOS[scenarioRef.current] || SCENARIOS.port_strike

    // Draw routes
    cfg.routes.forEach(route => {
      const pts = buildPath(route)
      if (!pts || pts.length < 2) return
      const st = STYLES[route.state]

      // Glow halo behind the line
      Lf.polyline(pts, {
        color: st.color, weight: st.weight + 8, opacity: 0.12,
      }).addTo(layerGroupRef.current)

      // Main line
      Lf.polyline(pts, {
        color: st.color, weight: st.weight, opacity: st.opacity,
        dashArray: st.dash, lineCap: 'round', lineJoin: 'round',
      }).addTo(layerGroupRef.current)
    })

    // Node markers
    cfg.activeNodes.forEach(key => {
      const n = NODES[key]
      Lf.marker([n.lat, n.lng], {
        icon: Lf.divIcon({
          html: nodeHtml(n, key === cfg.blockedNode),
          className: '',
          iconSize: [1, 1],
          iconAnchor: [6, 6],
        }),
        zIndexOffset: 300,
      }).addTo(layerGroupRef.current)
    })

    // Blocked badge offset from the blocked node
    const bn = NODES[cfg.blockedNode]
    const [dlat, dlng] = cfg.badgeOffset
    Lf.marker([bn.lat + dlat, bn.lng + dlng], {
      icon: Lf.divIcon({
        html: badgeHtml(cfg.blockedLabel),
        className: '',
        iconSize: [1, 1],
        iconAnchor: [65, 0],
      }),
      zIndexOffset: 400,
    }).addTo(layerGroupRef.current)

    fitBounds()
  }

  function fitBounds() {
    if (!mapRef.current) return
    const cfg = SCENARIOS[scenarioRef.current] || SCENARIOS.port_strike
    try {
      mapRef.current.fitBounds(cfg.bounds, { padding: [30, 30], animate: true, duration: 0.9 })
    } catch (_) { /* ignore fitBounds errors if map not fully ready */ }
  }

  // ── Animation loop ────────────────────────────────────────────────────────
  function startAnimation() {
    function frame() {
      const Lf  = window.L
      const map = mapRef.current
      if (!map || !Lf || destroyedRef.current) return

      const phase = truckPhaseRef.current
      const cfg   = SCENARIOS[scenarioRef.current] || SCENARIOS.port_strike
      const bn    = NODES[cfg.blockedNode]

      // Build vehicle paths for current scenario
      const oceanPts  = gcPoints(NODES[cfg.vehicleOcean[0]], NODES[cfg.vehicleOcean[1]])
      const groundPts = cfg.vehicleGround.map(k => [NODES[k].lat, NODES[k].lng])

      if (phase === 'blocked') {
        const wobble = Math.sin(Date.now() / 850) * 0.08
        // Sit just above/beside the blocked node so both markers are visible
        const pos = [bn.lat + 1.5 + wobble, bn.lng + 1.2]
        const blockedLabel = cfg.blockedNode === 'sh_customs' ? 'CUSTOMS HOLD' : 'PORT HOLD'
        if (!movingMarkerRef.current) {
          movingMarkerRef.current = Lf.marker(pos, {
            icon: Lf.divIcon({ html: vehicleHtml('🚢', '#ff3b5c', blockedLabel), className: '', iconSize: [1,1], iconAnchor: [18, 42] }),
            zIndexOffset: 700,
          }).addTo(map)
        } else {
          movingMarkerRef.current.setLatLng(pos)
          movingMarkerRef.current.setIcon(
            Lf.divIcon({ html: vehicleHtml('🚢', '#ff3b5c', blockedLabel), className: '', iconSize: [1,1], iconAnchor: [18, 42] })
          )
        }

      } else if (phase === 'flying') {
        truckTRef.current = Math.min(1, truckTRef.current + 0.0015)
        const pos = lerpPath(oceanPts, truckTRef.current)
        // port_strike uses air freight; others use ocean freight
        const inTransitEmoji = scenarioRef.current === 'port_strike' ? '✈' : '🚢'
        const inTransitLabel = scenarioRef.current === 'port_strike' ? 'AIR FREIGHT' : scenarioRef.current === 'customs_delay' ? 'CLEARED · ENROUTE' : 'SEA FREIGHT'
        if (!movingMarkerRef.current) {
          movingMarkerRef.current = Lf.marker(pos, {
            icon: Lf.divIcon({ html: vehicleHtml(inTransitEmoji, '#00d4ff', inTransitLabel), className: '', iconSize: [1,1], iconAnchor: [18, 42] }),
            zIndexOffset: 800,
          }).addTo(map)
        } else {
          movingMarkerRef.current.setLatLng(pos)
          movingMarkerRef.current.setIcon(
            Lf.divIcon({ html: vehicleHtml(inTransitEmoji, '#00d4ff', inTransitLabel), className: '', iconSize: [1,1], iconAnchor: [18, 42] })
          )
        }
        if (truckTRef.current >= 1) onTruckPhaseChange('driving')

      } else if (phase === 'driving') {
        truckTRef.current = Math.min(1, truckTRef.current + 0.0012)
        const pos = lerpPath(groundPts, truckTRef.current)
        if (movingMarkerRef.current) {
          movingMarkerRef.current.setLatLng(pos)
          movingMarkerRef.current.setIcon(
            Lf.divIcon({ html: vehicleHtml('🚛', '#39d98a', 'REROUTING'), className: '', iconSize: [1,1], iconAnchor: [18, 42] })
          )
        }
        if (truckTRef.current >= 1) onTruckPhaseChange('arrived')

      } else if (phase === 'arrived') {
        const dest = NODES[cfg.vehicleGround[cfg.vehicleGround.length - 1]]
        if (movingMarkerRef.current) {
          movingMarkerRef.current.setLatLng([dest.lat, dest.lng])
          movingMarkerRef.current.setIcon(
            Lf.divIcon({ html: arrivedHtml(), className: '', iconSize: [1,1], iconAnchor: [19, 46] })
          )
        }
      }

      animFrameRef.current = requestAnimationFrame(frame)
    }

    animFrameRef.current = requestAnimationFrame(frame)
  }
}
