export interface WSMessage {
  type: string
  data: any
  ts?: number
}

export function connectWS(sessionId: number | string) {
  const token = localStorage.getItem('liveops_token') || ''
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(
    `${proto}://${location.host}/api/v1/live/${sessionId}/stream?token=${encodeURIComponent(token)}`,
  )

  const listeners: Record<string, ((msg: WSMessage) => void)[]> = {}
  const catchAll: ((msg: WSMessage) => void)[] = []

  ws.onmessage = (ev) => {
    try {
      const msg: WSMessage = JSON.parse(ev.data)
      catchAll.forEach((fn) => fn(msg))
      ;(listeners[msg.type] || []).forEach((fn) => fn(msg))
    } catch {
      // ignore binary/garbage
    }
  }

  ws.onerror = () => { /* eslint-disable no-console */ console.warn('[ws] error') }

  return {
    subscribe(type: string, handler: (msg: WSMessage) => void) {
      ;(listeners[type] ||= []).push(handler)
      return () => {
        listeners[type] = (listeners[type] || []).filter((h) => h !== handler)
      }
    },
    onAll(handler: (msg: WSMessage) => void) {
      catchAll.push(handler)
    },
    close() {
      try { ws.close() } catch { /* noop */ }
    },
    get readyState() { return ws.readyState },
  }
}
