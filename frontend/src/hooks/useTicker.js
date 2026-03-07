import { useState, useEffect } from 'react'

export function useTicker(startTime, stopped = false) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (!startTime) {
      setValue(0)
      return
    }
    if (stopped) {
      // Keep the last value frozen — don't clear it, don't tick
      return
    }
    const id = setInterval(() => {
      const mins = (Date.now() - startTime) / 60000
      setValue(Math.floor(mins * 1388))
    }, 120)
    return () => clearInterval(id)
  }, [startTime, stopped])

  return value
}
