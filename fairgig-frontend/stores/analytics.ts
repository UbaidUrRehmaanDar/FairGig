import { defineStore } from 'pinia'
import { ref } from 'vue'

import { useApi } from '../composables/useApi'

type AnalyticsKpis = {
  commission_trends: Array<{
    shift_date: string
    avg_commission_pct: number
    sample_size: number
  }>
  income_by_zone: Array<{
    city_zone: string
    total_net_received: number
    avg_net_received: number
    sample_size: number
    worker_count: number
  }>
  vulnerability_flags: Array<{
    worker_id: string
    full_name?: string | null
    city_zone?: string | null
    platform: string
    shift_date: string
    prev_net_received: number
    net_received: number
    income_drop_pct: number
  }>
  top_complaints: Array<{
    category: string
    total_count: number
    total_upvotes: number
  }>
}

const emptyKpis = (): AnalyticsKpis => ({
  commission_trends: [],
  income_by_zone: [],
  vulnerability_flags: [],
  top_complaints: []
})

export const useAnalyticsStore = defineStore('analytics', () => {
  const { authFetch } = useApi()

  const kpis = ref<AnalyticsKpis>(emptyKpis())
  const loading = ref(false)
  const error = ref('')

  const fetchKPIs = async () => {
    loading.value = true
    error.value = ''
    try {
      const data = await authFetch<Partial<AnalyticsKpis>>('/analytics/kpis')
      kpis.value = {
        commission_trends: Array.isArray(data?.commission_trends) ? data.commission_trends : [],
        income_by_zone: Array.isArray(data?.income_by_zone) ? data.income_by_zone : [],
        vulnerability_flags: Array.isArray(data?.vulnerability_flags) ? data.vulnerability_flags : [],
        top_complaints: Array.isArray(data?.top_complaints) ? data.top_complaints : []
      }
      return kpis.value
    } catch (e: any) {
      kpis.value = emptyKpis()
      error.value = e?.message || 'Failed to load analytics.'
      return kpis.value
    } finally {
      loading.value = false
    }
  }

  return {
    kpis,
    loading,
    error,
    fetchKPIs
  }
})
