import { useEffect, useRef } from 'react'

// ─── Nodes ────────────────────────────────────────────────────────────────────
const NODES = {
  // Scenario 1 — Port Strike (Long Beach)
  shanghai:    { lat: 31.23,  lng: 121.47,  label: 'Shanghai Port',      icon: '📦', color: '#7aa0be' },
  longbeach:   { lat: 33.75,  lng: -118.19, label: 'Long Beach Port',    icon: '🔴', color: '#ff3b5c' },
  lax:         { lat: 33.94,  lng: -118.41, label: 'LAX Airport',        icon: '✈',  color: '#00d4ff' },
  oakland:     { lat: 37.80,  lng: -122.27, label: 'Port of Oakland',    icon: '⚓', color: '#ffb340' },
  cupertino:   { lat: 37.33,  lng: -122.03, label: 'Apple — Cupertino',  icon: '🏭', color: '#00e676' },
  tucson:      { lat: 32.25,  lng: -110.93, label: 'Tucson Air Hub',     icon: '🏢', color: '#ffb340' },

  // Scenario 2 — Customs Delay (Shenzhen → LAX)
  shenzhen:    { lat: 22.54,  lng: 114.06,  label: 'Shenzhen Airport',   icon: '📦', color: '#7aa0be' },
  customs_sz:  { lat: 22.54,  lng: 114.06,  label: 'Shenzhen Customs ⚠', icon: '🔴', color: '#ff3b5c' },
  busan:       { lat: 35.10,  lng: 129.04,  label: 'Busan Port (alt)',   icon: '⚓', color: '#00d4ff' },
  dallas_smsg: { lat: 32.78,  lng: -96.80,  label: 'Samsung — Dallas',   icon: '🏭', color: '#00e676' },

  // Scenario 3 — Supplier Breach (Taiwan → NVIDIA)
  hsinchu:     { lat: 24.80,  lng: 120.97,  label: 'Hsinchu Fab (bankrupt)', icon: '🔴', color: '#ff3b5c' },
  suwon:       { lat: 37.26,  lng: 127.00,  label: 'SK Hynix — Suwon',  icon: '🏭', color: '#00d4ff' },
  lax_nvidia:  { lat: 33.94,  lng: -118.41, label: 'LAX — Freight',     icon: '✈',  color: '#ffb340' },
  santa_clara: { lat: 37.38,  lng: -121.97, label: 'NVIDIA — Santa Clara', icon: '🏭', color: '#00e676' },
}

// ─── Scenarios ────────────────────────────────────────────────────────────────
const SCENARIOS = {
  // Scenario 1: $12M semiconductors blocked at Long Beach (ILWU strike)
  // Primary route: Shanghai → Long Beach [BLOCKED]
  // Active reroute: Shanghai → LAX (air, 60%) + Shanghai → Oakland (sea, 40%)
  // Destination: Apple HQ, Cupertino CA
  // Backup: Tucson Air Hub (Hour-20 trigger)
  port_strike: {
    bounds: [[18, 100], [52, -135]],
    activeNodes: ['shanghai', 'longbeach', 'lax', 'oakland', 'cupertino', 'tucson'],
    blockedNode: 'longbeach',
    blockedLabel: '⚠ ILWU STRIKE · PORT BLOCKED',
    badgeOffset: [1.5, 1.0],
    routes: [
      { path: ['shanghai', 'longbeach'], state: 'blocked',  arc: true  },
      { path: ['shanghai', 'lax'],       state: 'active',   arc: true  },  // 60% air reroute
      { path: ['shanghai', 'oakland'],   state: 'proposed', arc: true  },  // 40% sea via Oakland
      { path: ['lax', 'cupertino'],      state: 'active',   arc: false },  // ground to Apple
      { path: ['oakland', 'cupertino'],  state: 'proposed', arc: false },  // ground from Oakland
    ],
    vehicleOcean:  ['shanghai', 'lax'],
    vehicleGround: ['lax', 'cupertino'],
  },

  // Scenario 2: $8M components held at Shenzhen Customs
  // Primary route: Shenzhen → LAX [BLOCKED by customs]
  // Active reroute: Shenzhen → (air, expedited broker) → LAX
  // Backup: Reroute via Busan to bypass Shenzhen hold
  // Destination: Samsung US — Dallas/Plano TX (Samsung America HQ)
  customs_delay: {
    bounds: [[15, 95], [55, -110]],
    activeNodes: ['shenzhen', 'customs_sz', 'busan', 'lax', 'dallas_smsg'],
    blockedNode: 'customs_sz',
    blockedLabel: '⚠ CUSTOMS HOLD · SHENZHEN',
    badgeOffset: [1.5, -2.0],
    routes: [
      { path: ['shenzhen', 'lax'],      state: 'blocked',  arc: true  },  // original route blocked
      { path: ['shenzhen', 'busan'],    state: 'proposed', arc: false },  // alternate: truck to Busan
      { path: ['busan', 'lax'],         state: 'active',   arc: true  },  // air freight from Busan
      { path: ['lax', 'dallas_smsg'],   state: 'active',   arc: false },  // ground to Samsung Dallas
    ],
    vehicleOcean:  ['busan', 'lax'],
    vehicleGround: ['lax', 'dallas_smsg'],
  },

  // Scenario 3: $20M Taiwan fab order cancelled (supplier bankruptcy)
  // Primary route: Hsinchu Fab → LAX → NVIDIA Santa Clara [CANCELLED]
  // Reroute: SK Hynix Suwon (Korea) → LAX → NVIDIA Santa Clara
  supplier_breach: {
    bounds: [[20, 100], [50, -130]],
    activeNodes: ['hsinchu', 'suwon', 'lax_nvidia', 'santa_clara'],
    blockedNode: 'hsinchu',
    blockedLabel: '⚠ CHIPTECH BANKRUPT · ORDER CANCELLED',
    badgeOffset: [1.5, -2.0],
    routes: [
      { path: ['hsinchu', 'lax_nvidia'],   state: 'blocked',  arc: true  },  // original route dead
      { path: ['suwon', 'lax_nvidia'],     state: 'active',   arc: true  },  // alt: Korea → LAX air
      { path: ['lax_nvidia', 'santa_clara'], state: 'active', arc: false },  // ground to NVIDIA
    ],
    vehicleOcean:  ['suwon', 'lax_nvidia'],
    vehicleGround: ['lax_nvidia', 'santa_clara'],
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
  const c = '#00e676'
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

// ─── ANIMATED FLOW PARTICLES ─────────────────────────────────────────────────
function createFlowParticle(color, type = 'data') {
  const icons = {
    data: '📊',
    cargo: '📦', 
    signal: '📡',
    money: '💰'
  }
  
  return `<div style="
    width: 12px;
    height: 12px;
    background: radial-gradient(circle, ${color}ff 0%, ${color}88 50%, ${color}22 100%);
    border-radius: 50%;
    box-shadow: 0 0 8px ${color}bb, inset 0 0 4px ${color}ff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 8px;
    animation: flowPulse 0.8s ease-in-out infinite alternate;
    pointer-events: none;
  ">${icons[type] || '•'}</div>`
}

function createConnectionPulse(color, intensity = 1) {
  const size = 8 + (intensity * 4)
  return `<div style="
    width: ${size}px;
    height: ${size}px;
    background: ${color};
    border-radius: 50%;
    opacity: 0;
    animation: connectionPulse 2s ease-out infinite;
    pointer-events: none;
  "></div>`
}

// Live activity indicators for nodes (enhanced with mock-style pulsing)
function createNodeActivityIndicator(node, blocked, activity = 'normal') {
  const activityColors = {
    high: '#00ff88',
    normal: '#00d4ff', 
    low: '#ffb340',
    blocked: '#ff3b5c'
  }
  
  const activityLevel = blocked ? 'blocked' : activity
  const color = activityColors[activityLevel]
  
  // Enhanced pulsing like mock's node glow
  const pulseIntensity = blocked ? 'strong' : activity === 'high' ? 'medium' : 'soft'
  
  return `<div style="position: relative; display: flex; flex-direction: column; align-items: center; gap: 3px;">
    <!-- Enhanced activity ring with mock-style timing -->
    <div style="position: absolute; top: -12px; left: -12px; width: 36px; height: 36px; 
      border: 2px solid ${color}44; border-radius: 50%; 
      animation: activityRing 2.5s ease-in-out infinite;"></div>
    
    <!-- Secondary pulse ring (like mock's double glow) -->
    <div style="position: absolute; top: -8px; left: -8px; width: 28px; height: 28px; 
      border: 1px solid ${color}22; border-radius: 50%; 
      animation: activityRing 3.2s ease-in-out infinite 0.8s;"></div>
    
    <!-- Breathing glow background -->
    <div style="position: absolute; top: -6px; left: -6px; width: 24px; height: 24px; 
      background: radial-gradient(circle, ${color}33 0%, ${color}11 50%, transparent 70%); 
      border-radius: 50%; animation: breatheGlow 2s ease-in-out infinite;"></div>
    
    <!-- Data stream indicators with wobble -->
    <div style="position: absolute; top: -18px; left: -18px; width: 48px; height: 48px;">
      <div style="position: absolute; width: 4px; height: 4px; background: ${color}; 
        border-radius: 50%; top: 2px; left: 22px; 
        animation: dataStream1 1.8s ease-in-out infinite, wobbleEffect1 3s ease-in-out infinite;"></div>
      <div style="position: absolute; width: 3px; height: 3px; background: ${color}88; 
        border-radius: 50%; top: 10px; right: 4px; 
        animation: dataStream2 2.3s ease-in-out infinite 0.4s, wobbleEffect2 4s ease-in-out infinite 0.2s;"></div>
      <div style="position: absolute; width: 3px; height: 3px; background: ${color}88; 
        border-radius: 50%; bottom: 8px; left: 8px; 
        animation: dataStream3 2.1s ease-in-out infinite 0.8s, wobbleEffect3 3.5s ease-in-out infinite 0.6s;"></div>
      <div style="position: absolute; width: 2px; height: 2px; background: ${color}66; 
        border-radius: 50%; top: 18px; right: 18px; 
        animation: dataStream1 1.5s ease-in-out infinite 1.2s, wobbleEffect1 2.8s ease-in-out infinite 1s;"></div>
    </div>
    
    ${nodeHtml(node, blocked).replace('<div style="display:flex', '<div style="position: relative; z-index: 2; display:flex')}
  </div>`
}

// ─── Hook ─────────────────────────────────────────────────────────────────────
export function useLeafletMap(containerRef, { scenario, truckPhase, onTruckPhaseChange, isActive }) {
  // All mutable state lives in refs — never causes re-renders
  const mapRef          = useRef(null)
  const layerGroupRef   = useRef(null)
  const flowLayerRef    = useRef(null)    // NEW: For animated flow effects
  const movingMarkerRef = useRef(null)
  const animFrameRef    = useRef(null)
  const truckTRef       = useRef(0)
  const truckPhaseRef   = useRef(truckPhase)
  const scenarioRef     = useRef(scenario)
  const readyRef        = useRef(false)
  const destroyedRef    = useRef(false)
  const flowParticlesRef = useRef([])     // NEW: Track animated particles

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
        
        /* Enhanced live animations inspired by mock */
        @keyframes flowPulse { 
          0% { transform: scale(0.7); opacity: 0.6; }
          25% { transform: scale(1.1); opacity: 0.9; box-shadow: 0 0 12px currentColor; }
          50% { transform: scale(1.4); opacity: 1; box-shadow: 0 0 20px currentColor; }
          75% { transform: scale(1.1); opacity: 0.9; }
          100% { transform: scale(0.7); opacity: 0.6; }
        }
        
        @keyframes connectionPulse {
          0% { transform: scale(0.2); opacity: 0.9; }
          30% { transform: scale(1.2); opacity: 0.7; }
          60% { transform: scale(2.2); opacity: 0.4; }
          100% { transform: scale(4); opacity: 0; }
        }
        
        @keyframes activityRing {
          0% { transform: scale(0.6) rotate(0deg); opacity: 0.5; border-width: 2px; }
          25% { transform: scale(0.9) rotate(90deg); opacity: 0.7; border-width: 1.5px; }
          50% { transform: scale(1.3) rotate(180deg); opacity: 0.9; border-width: 1px; }
          75% { transform: scale(1.7) rotate(270deg); opacity: 0.6; border-width: 0.5px; }
          100% { transform: scale(2.2) rotate(360deg); opacity: 0; border-width: 0px; }
        }
        
        @keyframes breatheGlow {
          0% { transform: scale(0.8); opacity: 0.4; }
          50% { transform: scale(1.2); opacity: 0.8; }
          100% { transform: scale(0.8); opacity: 0.4; }
        }
        
        /* Wobble effects like mock's truck movement */
        @keyframes wobbleEffect1 {
          0% { transform: translateX(0) translateY(0); }
          25% { transform: translateX(1px) translateY(-0.5px); }
          50% { transform: translateX(-0.5px) translateY(1px); }
          75% { transform: translateX(0.5px) translateY(-0.5px); }
          100% { transform: translateX(0) translateY(0); }
        }
        
        @keyframes wobbleEffect2 {
          0% { transform: translateX(0) translateY(0) rotate(0deg); }
          33% { transform: translateX(-0.8px) translateY(0.8px) rotate(2deg); }
          66% { transform: translateX(0.8px) translateY(-0.5px) rotate(-1deg); }
          100% { transform: translateX(0) translateY(0) rotate(0deg); }
        }
        
        @keyframes wobbleEffect3 {
          0% { transform: translateY(0) scale(1); }
          30% { transform: translateY(-1px) scale(1.1); }
          70% { transform: translateY(0.8px) scale(0.9); }
          100% { transform: translateY(0) scale(1); }
        }
        
        @keyframes dataStream1 {
          0% { transform: translateY(0) scale(0.4); opacity: 0; }
          15% { transform: translateY(-3px) scale(0.8); opacity: 0.7; }
          30% { transform: translateY(-6px) scale(1.2); opacity: 1; }
          70% { transform: translateY(-14px) scale(1.4); opacity: 0.8; }
          100% { transform: translateY(-24px) scale(0.2); opacity: 0; }
        }
        
        @keyframes dataStream2 {
          0% { transform: translateX(0) scale(0.4); opacity: 0; }
          20% { transform: translateX(3px) scale(0.9); opacity: 0.8; }
          40% { transform: translateX(7px) scale(1.3); opacity: 1; }
          80% { transform: translateX(14px) scale(1.1); opacity: 0.7; }
          100% { transform: translateX(22px) scale(0.3); opacity: 0; }
        }
        
        @keyframes dataStream3 {
          0% { transform: translate(0, 0) scale(0.5); opacity: 0; }
          25% { transform: translate(-2px, -2px) scale(0.8); opacity: 0.9; }
          50% { transform: translate(-5px, -5px) scale(1.2); opacity: 1; }
          80% { transform: translate(-12px, -12px) scale(1.4); opacity: 0.6; }
          100% { transform: translate(-20px, -20px) scale(0.1); opacity: 0; }
        }
        
        /* Enhanced route flow animations with dash offset like mock */
        .route-flow-active {
          animation: routeFlow 3s linear infinite, routePulse 2s ease-in-out infinite;
        }
        
        @keyframes routeFlow {
          0% { stroke-dashoffset: 0; }
          100% { stroke-dashoffset: -30; }
        }
        
        @keyframes routePulse {
          0% { opacity: 0.6; stroke-width: 3px; }
          50% { opacity: 0.9; stroke-width: 4px; }
          100% { opacity: 0.6; stroke-width: 3px; }
        }
        
        @keyframes dataBurst {
          0% { transform: scale(0) rotate(0deg); opacity: 1; }
          30% { transform: scale(0.8) rotate(120deg); opacity: 0.9; }
          60% { transform: scale(1.5) rotate(240deg); opacity: 0.6; }
          100% { transform: scale(3.2) rotate(360deg); opacity: 0; }
        }
        
        /* Shimmer effect for enhanced realism */
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
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

    // Draw enhanced routes with animated flows
    cfg.routes.forEach((route, routeIndex) => {
      const pts = buildPath(route)
      if (!pts || pts.length < 2) return
      const st = STYLES[route.state]

      // Glow halo behind the line
      Lf.polyline(pts, {
        color: st.color, weight: st.weight + 8, opacity: 0.12,
      }).addTo(layerGroupRef.current)

      // Main animated line with flow effect
      const mainLine = Lf.polyline(pts, {
        color: st.color, 
        weight: st.weight, 
        opacity: st.opacity,
        dashArray: route.state === 'active' ? '8,12' : st.dash, 
        lineCap: 'round', 
        lineJoin: 'round',
        className: route.state === 'active' ? 'route-flow-active' : `route-${route.state}`
      }).addTo(layerGroupRef.current)

      // Add flowing particles for active routes
      if (route.state === 'active') {
        const numParticles = 3
        for (let i = 0; i < numParticles; i++) {
          setTimeout(() => {
            createFlowingParticle(pts, st.color, routeIndex, i)
          }, i * 800) // Stagger particle creation
        }
      }
      
      // Add connection pulses at route endpoints for active routes
      if (route.state === 'active' || route.state === 'proposed') {
        const startNode = NODES[route.path[0]]
        const endNode = NODES[route.path[route.path.length - 1]]
        
        // Create pulse markers at connection points
        setTimeout(() => {
          const pulseMarker = Lf.marker([startNode.lat, startNode.lng], {
            icon: Lf.divIcon({
              html: createConnectionPulse(st.color, route.state === 'active' ? 1.2 : 0.8),
              className: '',
              iconSize: [20, 20],
              iconAnchor: [10, 10],
            }),
            zIndexOffset: 250,
          }).addTo(layerGroupRef.current)
          
          // Remove pulse after animation
          setTimeout(() => {
            if (layerGroupRef.current) pulseMarker.remove()
          }, 2000)
        }, routeIndex * 600)
      }
    })

    // Enhanced node markers with live activity indicators
    cfg.activeNodes.forEach(key => {
      const n = NODES[key]
      const isBlocked = key === cfg.blockedNode
      const activityLevel = isBlocked ? 'blocked' : 
        (key === 'shanghai' || key === 'shenzhen' || key === 'lax' || key === 'lax_nvidia' || key === 'busan') ? 'high' : 'normal'
      
      Lf.marker([n.lat, n.lng], {
        icon: Lf.divIcon({
          html: createNodeActivityIndicator(n, isBlocked, activityLevel),
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
    
    // Start periodic live effects for enhanced realism
    if (isActive) {
      addPeriodicLiveEffects()
    }
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
        const wobble = Math.sin(Date.now() / 850) * 0.05
        const pos = [bn.lat + 0.35 + wobble, bn.lng + 0.45]
        if (!movingMarkerRef.current) {
          movingMarkerRef.current = Lf.marker(pos, {
            icon: Lf.divIcon({ html: vehicleHtml('🚛', '#ff3b5c', 'HELD'), className: '', iconSize: [1,1], iconAnchor: [18, 42] }),
            zIndexOffset: 700,
          }).addTo(map)
        } else {
          movingMarkerRef.current.setLatLng(pos)
        }

      } else if (phase === 'flying') {
        truckTRef.current = Math.min(1, truckTRef.current + 0.0015)
        const pos = lerpPath(oceanPts, truckTRef.current)
        if (!movingMarkerRef.current) {
          movingMarkerRef.current = Lf.marker(pos, {
            icon: Lf.divIcon({ html: vehicleHtml('✈', '#00d4ff', 'IN TRANSIT'), className: '', iconSize: [1,1], iconAnchor: [18, 42] }),
            zIndexOffset: 800,
          }).addTo(map)
        } else {
          movingMarkerRef.current.setLatLng(pos)
          movingMarkerRef.current.setIcon(
            Lf.divIcon({ html: vehicleHtml('✈', '#00d4ff', 'IN TRANSIT'), className: '', iconSize: [1,1], iconAnchor: [18, 42] })
          )
        }
        if (truckTRef.current >= 1) onTruckPhaseChange('driving')

      } else if (phase === 'driving') {
        truckTRef.current = Math.min(1, truckTRef.current + 0.0012)
        const pos = lerpPath(groundPts, truckTRef.current)
        if (movingMarkerRef.current) {
          movingMarkerRef.current.setLatLng(pos)
          movingMarkerRef.current.setIcon(
            Lf.divIcon({ html: vehicleHtml('🚛', '#00e676', 'REROUTING'), className: '', iconSize: [1,1], iconAnchor: [18, 42] })
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

  // ── Create flowing particles along routes (enhanced like mock) ────────────
  function createFlowingParticle(pathPoints, color, routeIndex, particleIndex) {
    if (!layerGroupRef.current) return
    
    const Lf = window.L
    const particleTypes = ['data', 'cargo', 'signal', 'money']
    const particleType = particleTypes[particleIndex % particleTypes.length]
    
    let currentProgress = 0
    const baseSpeed = 0.008 + (Math.random() * 0.006) // Slower, more varied speed
    
    // Add pulsing trail effect
    const trailMarker = Lf.marker(pathPoints[0], {
      icon: Lf.divIcon({
        html: `<div style="
          width: 20px; height: 20px; border-radius: 50%; 
          background: radial-gradient(circle, ${color}22 0%, transparent 70%);
          animation: connectionPulse 3s ease-out infinite;
          pointer-events: none;
        "></div>`,
        className: '',
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      }),
      zIndexOffset: 550,
    }).addTo(layerGroupRef.current)
    
    const particleMarker = Lf.marker(pathPoints[0], {
      icon: Lf.divIcon({
        html: createFlowParticle(color, particleType),
        className: '',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
      zIndexOffset: 600,
    }).addTo(layerGroupRef.current)
    
    function animateParticle() {
      if (currentProgress >= 1 || !layerGroupRef.current) {
        particleMarker.remove()
        trailMarker.remove()
        // Restart particle after varied delay (like mock's wobble timing)
        setTimeout(() => {
          if (layerGroupRef.current) {
            createFlowingParticle(pathPoints, color, routeIndex, particleIndex)
          }
        }, 1500 + Math.random() * 4000) // More varied restart timing
        return
      }
      
      const position = lerpPath(pathPoints, currentProgress)
      
      // Add micro-wobble to particle movement (like mock's truck wobble)
      const wobble = Math.sin(Date.now() * 0.01 + particleIndex) * 0.0001
      const wobbledPos = [
        position[0] + wobble, 
        position[1] + wobble * 0.5
      ]
      
      particleMarker.setLatLng(wobbledPos)
      
      // Trail follows with slight delay
      const trailProgress = Math.max(0, currentProgress - 0.08)
      const trailPosition = lerpPath(pathPoints, trailProgress)
      trailMarker.setLatLng(trailPosition)
      
      // Variable speed (faster at start, slower at end like mock's bezier timing)
      const speedMultiplier = 1 - (currentProgress * 0.3)
      currentProgress += baseSpeed * speedMultiplier
      
      requestAnimationFrame(animateParticle)
    }
    
    requestAnimationFrame(animateParticle)
  }

  // ── Add periodic live effects (enhanced with mock-style timing) ───────────
  function addPeriodicLiveEffects() {
    if (!layerGroupRef.current || !readyRef.current) return
    
    const Lf = window.L
    const cfg = SCENARIOS[scenarioRef.current] || SCENARIOS.port_strike
    
    // Enhanced burst timing like mock's animation phases
    const burstInterval = 2500 + Math.random() * 4500
    
    setTimeout(() => {
      if (!layerGroupRef.current) return
      
      // Pick a random active node for data burst (weighted toward high-activity nodes)
      const weights = cfg.activeNodes.map(node => 
        node === 'shanghai' || node === 'lax' ? 3 : 1
      )
      const totalWeight = weights.reduce((a, b) => a + b, 0)
      let random = Math.random() * totalWeight
      let selectedIndex = 0
      
      for (let i = 0; i < weights.length; i++) {
        random -= weights[i]
        if (random <= 0) {
          selectedIndex = i
          break
        }
      }
      
      const randomNode = cfg.activeNodes[selectedIndex]
      const node = NODES[randomNode]
      
      // Create enhanced data burst effect with shimmer
      const burstMarker = Lf.marker([node.lat, node.lng], {
        icon: Lf.divIcon({
          html: `<div style="
            width: 35px; height: 35px; border: 2px solid ${node.color};
            border-radius: 50%; 
            background: radial-gradient(circle, ${node.color}33 0%, ${node.color}11 40%, transparent 70%),
                       linear-gradient(45deg, transparent 30%, ${node.color}22 50%, transparent 70%);
            background-size: 100% 100%, 200% 200%;
            animation: dataBurst 2s ease-out forwards, shimmer 1.5s ease-in-out;
            box-shadow: 0 0 20px ${node.color}66;
          "></div>`,
          className: '',
          iconSize: [35, 35],
          iconAnchor: [17.5, 17.5],
        }),
        zIndexOffset: 500,
      }).addTo(layerGroupRef.current)
      
      // Add multiple concentric rings for enhanced effect
      const secondaryBurst = Lf.marker([node.lat, node.lng], {
        icon: Lf.divIcon({
          html: `<div style="
            width: 50px; height: 50px; border: 1px solid ${node.color}44;
            border-radius: 50%; 
            background: radial-gradient(circle, transparent 60%, ${node.color}08 80%, transparent);
            animation: dataBurst 2.5s ease-out forwards 0.3s;
          "></div>`,
          className: '',
          iconSize: [50, 50],
          iconAnchor: [25, 25],
        }),
        zIndexOffset: 450,
      }).addTo(layerGroupRef.current)
      
      // Remove burst effects after animation
      setTimeout(() => {
        if (layerGroupRef.current) {
          burstMarker.remove()
          secondaryBurst.remove()
        }
      }, 2500)
      
      // Create data stream between nodes occasionally
      if (Math.random() > 0.6) {
        const targetNodes = cfg.activeNodes.filter(n => n !== randomNode)
        if (targetNodes.length > 0) {
          const targetNode = targetNodes[Math.floor(Math.random() * targetNodes.length)]
          createDataStreamBetweenNodes(randomNode, targetNode)
        }
      }
      
      // Schedule next burst with varied timing (like mock's scenario steps)
      addPeriodicLiveEffects()
    }, burstInterval)
  }

  // ── Create data stream between nodes (new feature) ──────────────────────
  function createDataStreamBetweenNodes(sourceKey, targetKey) {
    if (!layerGroupRef.current) return
    
    const Lf = window.L
    const sourceNode = NODES[sourceKey]
    const targetNode = NODES[targetKey]
    
    const pathPoints = gcPoints(sourceNode, targetNode, 40)
    let progress = 0
    const speed = 0.015
    
    const streamMarker = Lf.marker([sourceNode.lat, sourceNode.lng], {
      icon: Lf.divIcon({
        html: `<div style="
          width: 8px; height: 8px;
          background: linear-gradient(45deg, #00d4ff, #9b5de5);
          border-radius: 50%;
          box-shadow: 0 0 10px #00d4ffaa;
          animation: flowPulse 0.6s ease-in-out infinite;
        "></div>`,
        className: '',
        iconSize: [8, 8],
        iconAnchor: [4, 4],
      }),
      zIndexOffset: 650,
    }).addTo(layerGroupRef.current)
    
    function animateStream() {
      if (progress >= 1 || !layerGroupRef.current) {
        streamMarker.remove()
        return
      }
      
      const position = lerpPath(pathPoints, progress)
      streamMarker.setLatLng(position)
      progress += speed
      
      requestAnimationFrame(animateStream)
    }
    
    requestAnimationFrame(animateStream)
  }
}
