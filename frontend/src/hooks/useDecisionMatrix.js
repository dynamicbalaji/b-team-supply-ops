/**
 * useDecisionMatrix.js
 * ─────────────────────
 * Fetches the live decision matrix for a run from the backend API.
 *
 * Data flow:
 *   1. On mount (or when runId changes), fetches GET /api/runs/{runId}/decision-matrix
 *   2. Re-fetches whenever an SSE "approval_required" event fires
 *      (so the matrix updates the moment the backend has a recommendation)
 *   3. Re-fetches on a short poll interval while the run is active
 *      to pick up intermediate agent outputs (mc_stats, freight options)
 *
 * Returns { options, mcStats, recommended, approval, loading, error }
 *
 * Usage in DecisionTab.jsx:
 *   const { options, mcStats, recommended, loading } = useDecisionMatrix(runId, isRunning, approvalData)
 */

import { useState, useEffect, useRef, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/** Poll interval (ms) while a run is active. */
const POLL_INTERVAL_ACTIVE = 4_000
/** Poll interval (ms) after run completes (slower — data is stable). */
const POLL_INTERVAL_DONE   = 30_000

export function useDecisionMatrix(runId, isRunning, approvalData) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const timerRef              = useRef(null)
  const mountedRef            = useRef(true)

  const fetchMatrix = useCallback(async () => {
    if (!runId) return
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/runs/${runId}/decision-matrix`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      if (mountedRef.current) {
        setData(json)
        setError(null)
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message)
      }
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [runId])

  // Initial fetch + polling while run is active
  useEffect(() => {
    mountedRef.current = true
    if (!runId) return

    fetchMatrix()

    const interval = isRunning ? POLL_INTERVAL_ACTIVE : POLL_INTERVAL_DONE
    timerRef.current = setInterval(fetchMatrix, interval)

    return () => {
      mountedRef.current = false
      clearInterval(timerRef.current)
    }
  }, [runId, isRunning, fetchMatrix])

  // Re-fetch immediately when approvalData arrives via SSE
  // (approval_required event means the matrix is now fully populated)
  useEffect(() => {
    if (approvalData && runId) {
      fetchMatrix()
    }
  }, [approvalData, runId, fetchMatrix])

  // Derive display values from fetched data, with sensible defaults
  const options     = data?.options     ?? []
  const mcStats     = data?.mc_stats    ?? { mean: 280000, p10: 241000, p90: 318000, ci: 0.94, distribution: [] }
  const recommended = data?.recommended ?? 'hybrid'
  const approval    = data?.approval    ?? approvalData  // SSE data as fallback

  return { options, mcStats, recommended, approval, loading, error, rawData: data }
}
