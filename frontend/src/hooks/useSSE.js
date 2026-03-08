import { useRef, useCallback } from 'react'

export function useSSE(onEvent) {
  const esRef = useRef(null)

  const connect = useCallback((runId) => {
    if (esRef.current) esRef.current.close()
    const url = `${import.meta.env.VITE_API_URL}/api/stream/${runId}`
    const es = new EventSource(url)

    es.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data)
        if (evt === 'ping' || evt.type === 'ping') return // ignore keepalive
        onEvent(evt)
      } catch (err) {
        console.warn('[useSSE] parse error:', err.message, '| raw:', e.data?.slice(0, 200))
      }
    }

    es.onerror = (err) => {
      console.warn('[useSSE] error — state:', es.readyState, err)
    }

    esRef.current = es
    return es
  }, [onEvent])

  const disconnect = useCallback(() => {
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }
  }, [])

  return { connect, disconnect }
}
