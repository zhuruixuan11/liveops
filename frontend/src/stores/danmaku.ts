import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DanmakuMessage, AgentAction, MonitorEvent } from '../types'

export const useDanmakuStore = defineStore('danmaku', () => {
  const sessionId = ref<number | null>(null)
  const danmakus = ref<DanmakuMessage[]>([])
  const agentActions = ref<AgentAction[]>([])
  const monitorEvents = ref<MonitorEvent[]>([])

  function reset(id?: number) {
    sessionId.value = id ?? null
    danmakus.value = []
    agentActions.value = []
    monitorEvents.value = []
  }

  function appendDanmaku(d: DanmakuMessage) {
    const arr = danmakus.value
    if (!arr.some((x) => String(x.id) === String(d.id))) {
      arr.push(d)
      if (arr.length > 500) arr.shift()
    }
  }

  function appendAgentAction(a: AgentAction) {
    const arr = agentActions.value
    if (!arr.some((x) => String(x.id) === String(a.id))) {
      arr.unshift(a)
      if (arr.length > 200) arr.pop()
    }
  }

  function appendMonitorEvent(m: MonitorEvent) {
    const arr = monitorEvents.value
    if (!arr.some((x) => String(x.id) === String(m.id))) {
      arr.unshift(m)
      if (arr.length > 100) arr.pop()
    }
  }

  return { sessionId, danmakus, agentActions, monitorEvents, reset, appendDanmaku, appendAgentAction, appendMonitorEvent }
})
