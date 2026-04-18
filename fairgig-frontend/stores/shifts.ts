import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

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

type AnomalyFinding = {
  date: string
  platform: string
  type: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  value: string | number | null
  explanation: string
}

type AnomalySummary = {
  shifts_analyzed: number
  high_priority_flags: number
  avg_commission_pct: number
  total_net: number
}

type AnomalyReport = {
  worker_id: string
  scanned_at: string | null
  service_status: string
  service_message: string | null
  summary: AnomalySummary
  findings_count: number
  findings: AnomalyFinding[]
  public_api?: {
    endpoint?: string
    description?: string
  }
}

type AnomalyReportView = {
  summary: string
  publicApiDescription: string
  serviceWarning: string
  scannedAt: string | null
  items: AnomalyFinding[]
  count: number
}

const emptyAnomalySummary = (): AnomalySummary => ({
  shifts_analyzed: 0,
  high_priority_flags: 0,
  avg_commission_pct: 0,
  total_net: 0,
})

const normalizeSeverity = (value: unknown): AnomalyFinding['severity'] => {
  const safe = String(value || '').toLowerCase().trim()
  if (safe === 'critical' || safe === 'high' || safe === 'low') {
    return safe
  }
  return 'medium'
}

const normalizeFindings = (items: unknown): AnomalyFinding[] => {
  if (!Array.isArray(items)) return []

  return items.map((item: any) => ({
    date: String(item?.date || ''),
    platform: String(item?.platform || 'Unknown platform'),
    type: String(item?.type || 'anomaly'),
    severity: normalizeSeverity(item?.severity),
    value:
      item?.value === null || item?.value === undefined ? null : (item?.value as string | number),
    explanation: String(item?.explanation || 'No explanation available.'),
  }))
}

const normalizeAnomalyReport = (payload: any): AnomalyReport => {
  const summaryRaw = payload?.summary || {}
  const findings = normalizeFindings(payload?.findings)

  return {
    worker_id: String(payload?.worker_id || ''),
    scanned_at: payload?.scanned_at ? String(payload.scanned_at) : null,
    service_status: String(payload?.service_status || 'ok'),
    service_message: payload?.service_message ? String(payload.service_message) : null,
    summary: {
      shifts_analyzed: Number(summaryRaw?.shifts_analyzed || 0),
      high_priority_flags: Number(summaryRaw?.high_priority_flags || 0),
      avg_commission_pct: Number(summaryRaw?.avg_commission_pct || 0),
      total_net: Number(summaryRaw?.total_net || 0),
    },
    findings_count: Number(payload?.findings_count || findings.length || 0),
    findings,
    public_api:
      payload?.public_api && typeof payload.public_api === 'object'
        ? {
            endpoint: payload.public_api?.endpoint ? String(payload.public_api.endpoint) : undefined,
            description: payload.public_api?.description
              ? String(payload.public_api.description)
              : undefined,
          }
        : undefined,
  }
}

export const useShiftsStore = defineStore('shifts', () => {
  const { authFetch } = useApi()

  const shifts = ref<ShiftRecord[]>([])
  const shiftsError = ref('')
  const summary = ref<ShiftSummary | null>(null)
  const summaryLoading = ref(false)
  const summaryError = ref('')
  const cityMedian = ref<any>(null)
  const loading = ref(false)
  const anomalies = ref<AnomalyFinding[]>([])
  const anomalyReportData = ref<AnomalyReport | null>(null)
  const anomalyError = ref('')
  const anomalyScannedAt = ref<string | null>(null)

  const anomalyReport = computed<AnomalyReportView>(() => {
    const report = anomalyReportData.value
    const serviceStatus = String(report?.service_status || '').trim()
    const serviceMessage = String(report?.service_message || '').trim()
    const count = report?.findings_count ?? anomalies.value.length

    const summary = anomalyError.value
      ? 'Anomaly scan unavailable.'
      : serviceStatus && serviceStatus !== 'ok'
        ? serviceMessage || 'Anomaly scan completed with warnings.'
        : count === 0
          ? 'No anomalies detected in recent shifts.'
          : `${count} ${count === 1 ? 'anomaly' : 'anomalies'} detected in recent shifts.`

    return {
      summary,
      publicApiDescription:
        report?.public_api?.description || 'Anomaly service: /anomaly/detect',
      serviceWarning: anomalyError.value
        ? `Service warning: ${anomalyError.value}`
        : serviceStatus && serviceStatus !== 'ok'
          ? `Service warning: ${serviceMessage || serviceStatus}`
          : '',
      scannedAt: report?.scanned_at || anomalyScannedAt.value,
      items: report?.findings || anomalies.value,
      count,
    }
  })

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

  const detectAnomalies = async (limit = 120) => {
    anomalyError.value = ''
    const safeLimit = Math.max(1, Math.min(240, Number(limit || 120)))

    try {
      const payload = await authFetch(`/shifts/anomaly-check?limit=${safeLimit}`)
      const normalized = normalizeAnomalyReport(payload)

      anomalyReportData.value = normalized
      anomalies.value = normalized.findings
      anomalyScannedAt.value = normalized.scanned_at || new Date().toISOString()

      if (normalized.service_status !== 'ok' && normalized.service_message) {
        anomalyError.value = normalized.service_message
      }

      return normalized
    } catch (error: any) {
      anomalyReportData.value = {
        worker_id: '',
        scanned_at: new Date().toISOString(),
        service_status: 'error',
        service_message: error?.message || 'Anomaly scan failed.',
        summary: emptyAnomalySummary(),
        findings_count: 0,
        findings: [],
      }
      anomalies.value = []
      anomalyError.value = error?.message || 'Anomaly scan failed.'
      anomalyScannedAt.value = new Date().toISOString()
      return anomalyReportData.value
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
    anomalyReport,
    anomalyError,
    anomalyScannedAt,
    fetchShifts,
    fetchSummary,
    fetchCityMedian,
    detectAnomalies,
    logShift,
  }
})