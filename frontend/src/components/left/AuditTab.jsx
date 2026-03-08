/**
 * AuditTab.jsx
 *
 * Decision Audit Trail — live, scenario-aware, animated.
 *
 * What changed vs the hardcoded version:
 *  1. Items come from the API (GET /api/runs/{runId}/audit-trail) and the
 *     live SSE "audit" stream, merged and deduplicated by useAuditTrail().
 *  2. Static STATIC_AUDIT_ITEMS is completely gone. The API fallback in
 *     routes_decision_audit.py serves the correct per-scenario items.
 *  3. Each audit card animates in with a staggered slide+fade whenever
 *     runId changes — same mechanic as the MC histogram and matrix rows.
 *     New items that arrive mid-run also animate in individually.
 *  4. A pulsing "live" dot appears at the bottom while isRunning is true.
 *  5. Loading skeletons shown while the first API fetch is in flight.
 */

import { useState, useEffect, useRef } from 'react'
import { useAuditTrail } from '../../hooks/useAuditTrail'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── PDF export ────────────────────────────────────────────────────────────

async function handleExportPDF(runId) {
  if (!runId) { alert('No active run to export.'); return }
  const url = `${API_BASE}/api/runs/${runId}/audit-trail/pdf`
  try {
    const probe = await fetch(url, { method: 'HEAD' }).catch(() => null)
    if (probe?.ok) window.open(url, '_blank')
    else window.print()
  } catch { window.print() }
}

// ── Shimmer skeleton card ─────────────────────────────────────────────────

function AuditSkeleton() {
  return (
    <div className="atl">
      {[1, 0.6, 0.3].map((op, n) => (
        <div key={n} className="aitem" style={{ opacity: op }}>
          <div className="adot" style={{ background: '#1a3a52', borderColor: '#1a3a52' }} />
          <div className="atime" style={{ background: '#0d2233', borderRadius: '3px', width: '110px', height: '9px' }} />
          <div className="acard">
            <div style={{ background: '#1a3a52', borderRadius: '3px', width: '130px', height: '10px', marginBottom: '5px' }} />
            <div style={{ background: '#0d2233', borderRadius: '3px', width: '88%', height: '9px' }} />
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Single animated audit item ────────────────────────────────────────────
// animKey = runId — changing it resets the animation so items re-enter on
// every new run, exactly like the MC histogram bars do.

function AuditItem({ item, idx, animKey }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    setVisible(false)
    // Stagger: first item appears quickly, later ones follow at 150ms each
    const t = setTimeout(() => setVisible(true), 40 + idx * 150)
    return () => clearTimeout(t)
  }, [animKey, idx])

  const color = item.agent_color || item.color || '#00d4ff'
  const label = item.agent_label || item.agent || ''
  const desc  = item.description || item.desc  || ''
  const data  = item.data        || ''
  const mem   = item.memory_note || item.memory || null
  const time  = item.time_label  || item.time   || ''

  return (
    <div
      className="aitem"
      style={{
        opacity:    visible ? 1 : 0,
        transform:  visible ? 'translateY(0)' : 'translateY(10px)',
        transition: `opacity 0.4s ease ${idx * 0.08}s, transform 0.4s ease ${idx * 0.08}s`,
      }}
    >
      <div className="adot" style={{ background: color, borderColor: color }} />
      <div className="atime">{time}</div>
      <div className="acard">
        <div className="aagent" style={{ color }}>{label}</div>
        <div className="adesc">{desc}</div>
        {data && <div className="adata">{data}</div>}
        {mem  && <div className="membadge">{mem}</div>}
      </div>
    </div>
  )
}

// ── Live tail indicator (pulsing while agents run) ────────────────────────

function LiveTail() {
  return (
    <div className="aitem" style={{ opacity: 0.45 }}>
      <div
        className="adot"
        style={{
          background: '#39d98a', borderColor: '#39d98a',
          animation: 'pulse 1.4s ease-in-out infinite',
        }}
      />
      <div
        className="atime"
        style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: '#3d5a72' }}
      >
        live
      </div>
      <div className="acard">
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: '#3d5a72' }}>
          Agents are running…
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────────────────

export default function AuditTab({ runId, auditItems = [], scenario, isRunning }) {
  const { items, loading } = useAuditTrail(runId, isRunning, auditItems)

  // animKey drives the stagger re-trigger: changes on every new run
  // so all cards slide in fresh, same as the MC chart bars do.
  const animKey = runId || 'idle'

  return (
    <div className="aud">
      <div className="sec-hd">
        <div className="sec-ttl">Decision Audit Trail</div>
        <button className="expbtn" onClick={() => handleExportPDF(runId)}>
          ⬇ Export PDF
        </button>
      </div>

      {/* Loading state */}
      {loading && items.length === 0 && (
        <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', height:'160px', gap:'12px' }}>
          <img src="/shield-icon.png" alt="Loading" className="loading-shield-icon" />
          <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>Fetching audit trail…</div>
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && (
        <div style={{
          display:'flex', flexDirection:'column', alignItems:'center',
          justifyContent:'center', height:'200px', gap:'10px', opacity:.35,
        }}>
          <img src="/shield-icon.png" alt="" className="empty-shield-icon" />
          <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'11px', color:'#3d5a72' }}>
            {runId ? 'Waiting for agents…' : 'Run a scenario to see the audit trail'}
          </div>
        </div>
      )}

      {/* Audit timeline — each item animates in, re-triggers on new run */}
      {items.length > 0 && (
        <div className="atl">
          {items.map((item, idx) => (
            <AuditItem
              key={`${animKey}-${idx}`}
              item={item}
              idx={idx}
              animKey={animKey}
            />
          ))}

          {isRunning && <LiveTail />}
        </div>
      )}
    </div>
  )
}
