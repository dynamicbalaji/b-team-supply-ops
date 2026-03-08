/**
 * MemoryTab.jsx
 *
 * Displays all rows from the `episodic_memory` TursoDB table.
 * - Fetches from GET /api/memory?sort_by=<col>&order=<dir>
 * - Latest item (by date_label) shown at top by default
 * - Column-header click toggles sort asc/desc
 * - Falls back to in-memory seed data when TursoDB is not configured
 */

import { useState, useEffect, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Date formatting ────────────────────────────────────────────────────────
// Converts "2026-03-06" → "06th Mar 2026"

function ordinalSuffix(day) {
  if (day >= 11 && day <= 13) return 'th'
  switch (day % 10) {
    case 1: return 'st'
    case 2: return 'nd'
    case 3: return 'rd'
    default: return 'th'
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr + 'T00:00:00Z')
  if (isNaN(d.getTime())) return isoStr   // fallback: show raw string
  const day  = d.getUTCDate()
  const mon  = d.toLocaleDateString('en-GB', { month: 'short', timeZone: 'UTC' })
  const year = d.getUTCFullYear()
  return `${String(day).padStart(2, '0')}${ordinalSuffix(day)} ${mon} ${year}`
}

const SCENARIO_COLORS = {
  port_strike:     '#ff3b5c',
  customs_delay:   '#ffb340',
  supplier_breach: '#9b5de5',
}

const SCENARIO_LABELS = {
  port_strike:     'Port Strike',
  customs_delay:   'Customs Delay',
  supplier_breach: 'Supplier Breach',
}

const COLUMNS = [
  { key: 'date_label',    label: 'Date',         width: '90px'  },
  { key: 'scenario_type', label: 'Scenario',      width: '110px' },
  { key: 'crisis',        label: 'Crisis',        width: null    },
  { key: 'cost_usd',      label: 'Cost',          width: '72px'  },
  { key: 'saved_usd',     label: 'Saved',         width: '72px'  },
  { key: 'confidence',    label: 'Conf.',         width: '55px'  },
]

function fmt(n) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `$${Math.round(n / 1_000)}K`
  return `$${n}`
}

function SortIcon({ col, sortBy, order }) {
  if (sortBy !== col) return <span style={{ color: '#1d2d40', marginLeft: 3 }}>⇅</span>
  return (
    <span style={{ color: '#00d4ff', marginLeft: 3 }}>
      {order === 'desc' ? '↓' : '↑'}
    </span>
  )
}

function MemorySkeleton() {
  return (
    <div style={{ padding: '0 4px' }}>
      {[1, 0.6, 0.35].map((op, i) => (
        <div
          key={i}
          style={{
            opacity: op,
            background: '#111820',
            border: '1px solid #1d2d40',
            borderRadius: 6,
            padding: '10px 12px',
            marginBottom: 8,
            display: 'flex',
            gap: 10,
          }}
        >
          <div style={{ width: 80, height: 9, background: '#1a3a52', borderRadius: 3 }} />
          <div style={{ width: 90, height: 9, background: '#1a3a52', borderRadius: 3 }} />
          <div style={{ flex: 1, height: 9, background: '#0d2233', borderRadius: 3 }} />
        </div>
      ))}
    </div>
  )
}

function MemoryCard({ mem, idx, animKey }) {
  const [visible, setVisible] = useState(false)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    setVisible(false)
    const t = setTimeout(() => setVisible(true), 40 + idx * 100)
    return () => clearTimeout(t)
  }, [animKey, idx])

  const color = SCENARIO_COLORS[mem.scenario_type] || '#00d4ff'
  const confPct = Math.round((mem.confidence || 0) * 100)

  return (
    <div
      style={{
        opacity:    visible ? 1 : 0,
        transform:  visible ? 'translateY(0)' : 'translateY(8px)',
        transition: `opacity 0.35s ease ${idx * 0.06}s, transform 0.35s ease ${idx * 0.06}s`,
        background: '#111820',
        border:     `1px solid #1d2d40`,
        borderLeft: `3px solid ${color}`,
        borderRadius: 6,
        marginBottom: 8,
        cursor: 'pointer',
        overflow: 'hidden',
      }}
      onClick={() => setExpanded(e => !e)}
    >
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 11px' }}>
        {/* Date */}
        <div style={{
          fontFamily: "'JetBrains Mono',monospace",
          fontSize: 10,
          color: '#3d5a72',
          minWidth: 88,
          flexShrink: 0,
          title: mem.date || '',
        }}>
          {formatDate(mem.date)}
        </div>

        {/* Scenario badge */}
        <div style={{
          background: `${color}18`,
          border: `1px solid ${color}44`,
          borderRadius: 3,
          padding: '2px 7px',
          fontSize: 9,
          fontWeight: 700,
          color,
          fontFamily: "'JetBrains Mono',monospace",
          flexShrink: 0,
          minWidth: 100,
          textAlign: 'center',
        }}>
          {SCENARIO_LABELS[mem.scenario_type] || mem.scenario_type}
        </div>

        {/* Crisis summary */}
        <div style={{
          flex: 1,
          fontSize: 10,
          color: '#7aa0be',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          fontFamily: "'JetBrains Mono',monospace",
        }}>
          {mem.crisis}
        </div>

        {/* Cost */}
        <div style={{
          fontFamily: "'JetBrains Mono',monospace",
          fontSize: 10,
          color: '#ff3b5c',
          minWidth: 60,
          textAlign: 'right',
          flexShrink: 0,
        }}>
          {fmt(mem.cost_usd || 0)}
        </div>

        {/* Saved */}
        <div style={{
          fontFamily: "'JetBrains Mono',monospace",
          fontSize: 10,
          color: '#39d98a',
          minWidth: 60,
          textAlign: 'right',
          flexShrink: 0,
        }}>
          +{fmt(mem.saved_usd || 0)}
        </div>

        {/* Confidence */}
        <div style={{
          fontFamily: "'JetBrains Mono',monospace",
          fontSize: 10,
          color: confPct >= 90 ? '#39d98a' : confPct >= 80 ? '#ffb340' : '#ff3b5c',
          minWidth: 42,
          textAlign: 'right',
          flexShrink: 0,
        }}>
          {confPct}%
        </div>

        {/* Expand chevron */}
        <div style={{ color: '#3d5a72', fontSize: 10, marginLeft: 4, flexShrink: 0 }}>
          {expanded ? '▲' : '▼'}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{
          borderTop: '1px solid #1d2d40',
          padding: '10px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: 7,
        }}>
          <DetailRow label="Decision" value={mem.decision} color="#00d4ff" />
          <DetailRow label="Outcome"  value={mem.outcome}  color="#39d98a" />
          <DetailRow label="Learning" value={mem.key_learning} color="#ffb340" />
        </div>
      )}
    </div>
  )
}

function DetailRow({ label, value, color }) {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
      <div style={{
        fontFamily: "'JetBrains Mono',monospace",
        fontSize: 9,
        color: '#3d5a72',
        textTransform: 'uppercase',
        letterSpacing: '0.8px',
        minWidth: 62,
        paddingTop: 1,
        flexShrink: 0,
      }}>
        {label}
      </div>
      <div style={{
        fontSize: 10,
        color: color || '#7aa0be',
        lineHeight: 1.5,
        fontFamily: "'JetBrains Mono',monospace",
      }}>
        {value || '—'}
      </div>
    </div>
  )
}

// Sort controls header
function SortHeader({ sortBy, order, onSort }) {
  const sortableCols = ['date_label', 'scenario_type', 'cost_usd', 'saved_usd', 'confidence']

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 4,
      marginBottom: 10,
      paddingBottom: 8,
      borderBottom: '1px solid #1d2d40',
      flexWrap: 'wrap',
    }}>
      <span style={{
        fontFamily: "'JetBrains Mono',monospace",
        fontSize: 9,
        color: '#3d5a72',
        textTransform: 'uppercase',
        letterSpacing: '1px',
        marginRight: 4,
      }}>
        Sort:
      </span>
      {sortableCols.map(col => {
        const labels = {
          date_label:    'Date',
          scenario_type: 'Scenario',
          cost_usd:      'Cost',
          saved_usd:     'Saved',
          confidence:    'Confidence',
        }
        const active = sortBy === col
        return (
          <button
            key={col}
            onClick={() => onSort(col)}
            style={{
              background:  active ? 'rgba(0,212,255,0.1)' : '#111820',
              border:      `1px solid ${active ? '#00d4ff' : '#1d2d40'}`,
              borderRadius: 4,
              padding:     '3px 8px',
              fontSize:    9,
              color:       active ? '#00d4ff' : '#3d5a72',
              cursor:      'pointer',
              fontFamily:  "'JetBrains Mono',monospace",
              display:     'flex',
              alignItems:  'center',
              gap:         2,
              transition:  'all 0.15s',
            }}
          >
            {labels[col]}
            <SortIcon col={col} sortBy={sortBy} order={order} />
          </button>
        )
      })}
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────

export default function MemoryTab() {
  const [memories, setMemories]   = useState([])
  const [loading,  setLoading]    = useState(false)
  const [error,    setError]      = useState(null)
  const [sortBy,   setSortBy]     = useState('date_label')
  const [order,    setOrder]      = useState('desc')
  const [fetchKey, setFetchKey]   = useState(0)   // bump to refetch

  const fetchMemories = useCallback(async (col, dir) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `${API_BASE}/api/memory?sort_by=${col}&order=${dir}`,
        { signal: AbortSignal.timeout(8000) }
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setMemories(data.memories || [])
    } catch (err) {
      setError(err.message)
      setMemories([])
    } finally {
      setLoading(false)
    }
  }, [])

  // Re-fetch whenever sort params change
  useEffect(() => {
    fetchMemories(sortBy, order)
  }, [sortBy, order, fetchKey, fetchMemories])

  function handleSort(col) {
    if (sortBy === col) {
      // Toggle direction
      setOrder(o => (o === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortBy(col)
      setOrder('desc')
    }
  }

  const animKey = `${sortBy}-${order}`

  return (
    <div className="aud" style={{ padding: 16, overflowY: 'auto', flex: 1 }}>
      {/* Header */}
      <div className="sec-hd" style={{ marginBottom: 10 }}>
        <div className="sec-ttl">Episodic Memory</div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {/* Total badge */}
          {memories.length > 0 && (
            <span className="bdg bgrn" style={{ fontSize: 9 }}>
              {memories.length} records
            </span>
          )}
          {/* Refresh button */}
          <button
            className="expbtn"
            onClick={() => setFetchKey(k => k + 1)}
            title="Refresh"
          >
            ↺ Refresh
          </button>
        </div>
      </div>

      {/* Sort controls */}
      <SortHeader sortBy={sortBy} order={order} onSort={handleSort} />

      {/* Column labels */}
      <div style={{
        display: 'flex',
        gap: 8,
        padding: '0 11px 6px',
        borderBottom: '1px solid #1d2d40',
        marginBottom: 8,
      }}>
        {[
          { label: 'Date',     w: 88  },
          { label: 'Scenario', w: 108 },
          { label: 'Crisis',   w: null },
          { label: 'Cost',     w: 60  },
          { label: 'Saved',    w: 60  },
          { label: 'Conf.',    w: 42  },
          { label: '',         w: 20  },
        ].map(({ label, w }, i) => (
          <div
            key={i}
            style={{
              fontFamily: "'JetBrains Mono',monospace",
              fontSize: 8,
              color: '#3d5a72',
              textTransform: 'uppercase',
              letterSpacing: '0.8px',
              ...(w ? { minWidth: w, flexShrink: 0 } : { flex: 1 }),
              textAlign: i >= 3 ? 'right' : 'left',
            }}
          >
            {label}
          </div>
        ))}
      </div>

      {/* Loading state */}
      {loading && memories.length === 0 && (
        <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', height:'160px', gap:'12px' }}>
          <img src="/shield-icon.png" alt="Loading" className="loading-shield-icon" />
          <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#3d5a72' }}>Loading memories…</div>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div style={{
          background: 'rgba(255,59,92,0.08)',
          border: '1px solid rgba(255,59,92,0.25)',
          borderRadius: 6,
          padding: '12px 14px',
          fontSize: 10,
          color: '#ff3b5c',
          fontFamily: "'JetBrains Mono',monospace",
        }}>
          ⚠ Could not load memories: {error}
          <br />
          <span style={{ color: '#3d5a72', fontSize: 9 }}>
            Check that the backend is running and TursoDB is configured.
          </span>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && memories.length === 0 && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: 180,
          gap: 10,
          opacity: 0.35,
        }}>
          <img src="/shield-icon.png" alt="" className="empty-shield-icon" />
          <div style={{
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 11,
            color: '#3d5a72',
          }}>
            No episodic memories found
          </div>
        </div>
      )}

      {/* Memory cards */}
      {memories.map((mem, idx) => (
        <MemoryCard
          key={`${animKey}-${mem.memory_key}`}
          mem={mem}
          idx={idx}
          animKey={animKey}
        />
      ))}

      {/* Legend */}
      {memories.length > 0 && (
        <div style={{
          marginTop: 12,
          paddingTop: 10,
          borderTop: '1px solid #1d2d40',
          display: 'flex',
          gap: 14,
          flexWrap: 'wrap',
        }}>
          {Object.entries(SCENARIO_COLORS).map(([k, c]) => (
            <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: c }} />
              <span style={{
                fontFamily: "'JetBrains Mono',monospace",
                fontSize: 8,
                color: '#3d5a72',
                textTransform: 'uppercase',
                letterSpacing: '0.8px',
              }}>
                {SCENARIO_LABELS[k]}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
