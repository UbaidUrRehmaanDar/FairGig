import { defineStore } from 'pinia'
import { ref } from 'vue'

import { useApi } from '../composables/useApi'

type ShiftRecord = {
  id: string
  worker_id: string
  platform: string
  shift_date: string
  hours_worked: number | null
  gross_earned: number
  platform_deductions: number
  net_received: number
  verification_status?: string
  notes?: string | null
}

type ShiftSummary = {
  this_month: number
  this_week: number
  avg_hourly: number
  avg_commission_pct: number
  total_shifts: number
}

export const useShiftsStore = defineStore('shifts', () => {
  const { authFetch } = useApi()
  const config = useRuntimeConfig()
  const supabase = useSupabaseClient()

  const shifts = ref<ShiftRecord[]>([])
  const shiftsError = ref('')
  const summary = ref<ShiftSummary | null>(null)
  const summaryLoading = ref(false)
  const summaryError = ref('')
  const cityMedian = ref<any>(null)
  const loading = ref(false)
  const anomalies = ref<any[]>([])
  const anomalyError = ref('')
  const anomalyScannedAt = ref<string | null>(null)

  const getCurrentUserId = async () => {
    const { data } = await supabase.auth.getSession()
    const userId = data.session?.user?.id
    return typeof userId === 'string' ? userId.trim() : ''
  }

  const fetchShifts = async () => {
    loading.value = true
    shiftsError.value = ''
    try {
      const data = await authFetch<ShiftRecord[]>('/shifts')
      shifts.value = Array.isArray(data) ? data : []
      return shifts.value
    } catch (error: any) {
      shifts.value = []
      shiftsError.value = error?.message || 'Failed to load shifts.'
      return shifts.value
    } finally {
      loading.value = false
    }
  }

  const fetchSummary = async () => {
    summaryLoading.value = true
    summaryError.value = ''

    try {
      const data = await authFetch<Partial<ShiftSummary>>('/shifts/summary')
      summary.value = {
        this_month: Number(data?.this_month || 0),
        this_week: Number(data?.this_week || 0),
        avg_hourly: Number(data?.avg_hourly || 0),
        avg_commission_pct: Number(data?.avg_commission_pct || 0),
        total_shifts: Number(data?.total_shifts || 0),
      }
      return summary.value
    } catch (error: any) {
      // Prevent the UI from skeleton-loading forever.
      summary.value = {
        this_month: 0,
        this_week: 0,
        avg_hourly: 0,
        avg_commission_pct: 0,
        total_shifts: 0,
      }
      summaryError.value = error?.message || 'Failed to load shift summary.'
      return summary.value
    } finally {
      summaryLoading.value = false
    }
  }

  const fetchCityMedian = async (platform?: string) => {
    const targetPlatform = String(platform || shifts.value?.[0]?.platform || '').trim()
    if (!targetPlatform) {
      cityMedian.value = null
      return null
    }

    const qs = encodeURIComponent(targetPlatform)
    cityMedian.value = await authFetch(`/shifts/city-median?platform=${qs}`)
    return cityMedian.value
  }

  const detectAnomalies = async (limit = 25) => {
    anomalyError.value = ''

    const currentUserId = await getCurrentUserId()
    const workerId = currentUserId || String(shifts.value?.[0]?.worker_id || '').trim()
    const earnings = (shifts.value || [])
      .slice(0, limit)
      .map((shift) => ({
        date: shift.shift_date,
        platform: shift.platform,
        gross_earned: Number(shift.gross_earned || 0),
        platform_deductions: Number(shift.platform_deductions || 0),
        net_received: Number(shift.net_received || 0),
        hours_worked: shift.hours_worked == null ? null : Number(shift.hours_worked),
      }))
      .filter((item) => !!item.date)

    if (!workerId || earnings.length < 2) {
      anomalies.value = []
      anomalyScannedAt.value = new Date().toISOString()
      return anomalies.value
    }

    const anomalyBase = String(config.public.anomalyBase || 'http://localhost:8001').replace(
      /\/$/,
      ''
    )

    try {
      const response = await fetch(`${anomalyBase}/anomaly/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          worker_id: workerId,
          earnings,
        }),
      })

      const payload = await response.json().catch(() => null)
      if (!response.ok) {
        const detail =
          payload && typeof payload === 'object' && 'detail' in payload
            ? String((payload as any).detail)
            : ''
        throw new Error(detail || `Anomaly service failed (${response.status})`)
      }

      anomalies.value = Array.isArray(payload?.anomalies) ? payload.anomalies : []
      anomalyScannedAt.value = new Date().toISOString()
      return anomalies.value
    } catch (error: any) {
      anomalies.value = []
      anomalyError.value = error?.message || 'Anomaly scan failed.'
      anomalyScannedAt.value = new Date().toISOString()
      return anomalies.value
    }
  }

  const logShift = async (payload?: any) => {
    const result = await authFetch('/shifts', {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    })

    await fetchShifts()
    await fetchSummary()
    await fetchCityMedian(payload?.platform)
    await detectAnomalies()

    return result
  }

  return {
    shifts,
    shiftsError,
    summary,
    summaryLoading,
    summaryError,
    cityMedian,
    loading,
    anomalies,
    anomalyError,
    anomalyScannedAt,
    fetchShifts,
    fetchSummary,
    fetchCityMedian,
    detectAnomalies,
    logShift,
  }
})
