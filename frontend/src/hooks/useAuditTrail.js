/**
 * useAuditTrail.js
 * ─────────────────
 * Fetches the live audit trail for a run from the backend API.
 *
 * Data flow:
 *   1. Merges SSE "audit" events received in real time (prop: liveAuditItems)
 *      with whatever the REST endpoint returns on initial load / reconnect.
 *   2. The SSE path is the primary source during an active run (low-latency).
 *   3. On mount, a REST fetch hydrates items from before the component mounted
 *      (e.g. page refresh mid-run, or viewing a completed run).
 *   4. Items are deduplicated by time_label to avoid double-rendering when
 *      both the SSE stream and REST poll return the same entry.
 *
 * Usage in AuditTab.jsx:
 *   const { items, loading } = useAuditTrail(runId, isRunning, liveAuditItems)
 */

import { useState, useEffect, useRef, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const POLL_INTERVAL = 8_000   // Poll every 8s while run is active

/** Merge and deduplicate two lists of audit items by time_label. */
function mergeItems(apiItems, sseItems) {
  const seen = new Set()
  const all  = [...apiItems, ...sseItems]
  return all.filter(item => {
    const key = item.time_label || item.time || `${item.agent_label}-${item.description}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

/** Normalize an SSE "audit" event from App.jsx into the display shape. */
function normalizeSSEItem(evt) {
  // SSE events arrive as { type:"audit", time_label, agent_color, agent_label,
  //                        description, data, memory_note, elapsed_s }
  // Legacy App.jsx shape: { time, agentColor, agentLabel, description, data, hasMemory }
  return {
    time_label:  evt.time_label  || evt.time        || '',
    agent_color: evt.agent_color || evt.agentColor  || '#00d4ff',
    agent_label: evt.agent_label || evt.agentLabel  || '',
    description: evt.description || '',
    data:        evt.data        || '',
    memory_note: evt.memory_note ?? (
      evt.hasMemory
        ? `📚 ${evt.description?.split('Memory recalled')[1]?.trim() || 'Memory context available'}`
        : null
    ),
  }
}

export function useAuditTrail(runId, isRunning, liveAuditItems = []) {
  const [apiItems, setApiItems]   = useState([])
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const timerRef                  = useRef(null)
  const mountedRef                = useRef(true)

  const fetchTrail = useCallback(async () => {
    if (!runId) return
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/runs/${runId}/audit-trail`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      if (mountedRef.current) {
        setApiItems(json.items || [])
        setError(null)
      }
    } catch (err) {
      if (mountedRef.current) setError(err.message)
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [runId])

  // Initial fetch + periodic refresh
  useEffect(() => {
    mountedRef.current = true
    if (!runId) return

    fetchTrail()

    if (isRunning) {
      timerRef.current = setInterval(fetchTrail, POLL_INTERVAL)
    }

    return () => {
      mountedRef.current = false
      clearInterval(timerRef.current)
    }
  }, [runId, isRunning, fetchTrail])

  // Normalize live SSE items
  const normalizedSSE = liveAuditItems.map(normalizeSSEItem)

  // Merged result: API items provide the historical baseline,
  // SSE items extend it in real time
  const items = mergeItems(apiItems, normalizedSSE)

  return { items, loading, error }
}
