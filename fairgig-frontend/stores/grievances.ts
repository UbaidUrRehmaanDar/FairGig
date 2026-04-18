import { defineStore } from 'pinia'
import { ref } from 'vue'

import { useApi } from '../composables/useApi'

type GrievanceItem = {
  id: string
  worker_id: string
  platform: string
  category: string
  title: string
  description: string
  tags: string[]
  status: string
  upvotes: number
  created_at: string
  updated_at: string
  full_name?: string | null
  city_zone?: string | null
}

type GrievanceListResponse = {
  items: GrievanceItem[]
  count: number
  filters: {
    platform: string | null
    category: string | null
    status: string | null
  }
}

type GrievanceFilters = {
  platform?: string
  category?: string
  status?: string
}

export const useGrievancesStore = defineStore('grievances', () => {
  const { authFetch } = useApi()

  const items = ref<GrievanceItem[]>([])
  const loading = ref(false)
  const error = ref('')
  const lastFilters = ref<GrievanceFilters>({})

  const fetch = async (filters: GrievanceFilters = {}) => {
    loading.value = true
    error.value = ''
    lastFilters.value = { ...filters }

    try {
      const params = new URLSearchParams()
      if (filters.platform) params.set('platform', filters.platform)
      if (filters.category) params.set('category', filters.category)
      if (filters.status) params.set('status', filters.status)

      const qs = params.toString()
      const response = await authFetch<GrievanceListResponse>(`/grievances${qs ? `?${qs}` : ''}`)
      items.value = Array.isArray(response?.items) ? response.items : []
      return items.value
    } catch (e: any) {
      items.value = []
      error.value = e?.message || 'Failed to load grievances.'
      return items.value
    } finally {
      loading.value = false
    }
  }

  const create = async (payload: any) => {
    const created = await authFetch<GrievanceItem>('/grievances', {
      method: 'POST',
      body: payload
    })

    await fetch(lastFilters.value)
    return created
  }

  const upvote = async (grievanceId: string) => {
    const result = await authFetch(`/grievances/${grievanceId}/upvote`, { method: 'POST' })
    await fetch(lastFilters.value)
    return result
  }

  const escalate = async (grievanceId: string) => {
    const result = await authFetch(`/grievances/${grievanceId}/escalate`, { method: 'PATCH' })
    await fetch(lastFilters.value)
    return result
  }

  return {
    items,
    loading,
    error,
    fetch,
    create,
    upvote,
    escalate
  }
})
