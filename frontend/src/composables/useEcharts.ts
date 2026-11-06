import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import type { Ref } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

export function useEcharts(containerRef: Ref<HTMLElement | null | undefined>, option: Ref<EChartsOption> | (() => EChartsOption)) {
  const chart = ref<echarts.ECharts | null>(null)

  const init = () => {
    if (!containerRef.value) return
    if (chart.value) return
    chart.value = echarts.init(containerRef.value)
    const opt = typeof option === 'function' ? option() : option.value
    if (opt) chart.value.setOption(opt)
  }

  const resize = () => chart.value?.resize()

  onMounted(() => {
    init()
    window.addEventListener('resize', resize)
  })

  if (typeof option !== 'function') {
    watch(option, (v) => {
      chart.value?.setOption(v, true)
    }, { deep: true })
  }

  onBeforeUnmount(() => {
    window.removeEventListener('resize', resize)
    chart.value?.dispose()
    chart.value = null
  })

  return { chart, resize }
}
