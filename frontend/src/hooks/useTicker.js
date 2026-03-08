import { useState, useEffect, useRef } from 'react'

/**
 * useTicker(startTime, isStopped)
 *
 * Accumulates a cost value at $1,388/min from startTime.
 * Freezes immediately when isStopped becomes true (e.g. after approval).
 */
export function useTicker(startTime, isStopped = false) {
  const [value, setValue] = useState(0)
  const frozenRef = useRef(null) // stores the frozen value once stopped

  useEffect(() => {
    if (!startTime) {
      setValue(0)
      frozenRef.current = null
      return
    }

    // If already stopped when effect runs, freeze immediately
    if (isStopped) {
      if (frozenRef.current === null) {
        const mins = (Date.now() - startTime) / 60000
        frozenRef.current = Math.floor(mins * 1388)
      }
      setValue(frozenRef.current)
      return
    }

    // Reset frozen ref if running again (new scenario)
    frozenRef.current = null

    const id = setInterval(() => {
      const mins = (Date.now() - startTime) / 60000
      setValue(Math.floor(mins * 1388))
    }, 120)

    return () => clearInterval(id)
  }, [startTime, isStopped])

  return value
}
