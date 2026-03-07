import { useState, useEffect } from 'react'

export function useTicker(startTime) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (!startTime) {
      setValue(0)
      return
    }
    const id = setInterval(() => {
      const mins = (Date.now() - startTime) / 60000
      setValue(Math.floor(mins * 1388))
    }, 120)
    return () => clearInterval(id)
  }, [startTime])

  return value // integer dollar amount
}
