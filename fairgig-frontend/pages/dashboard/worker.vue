<template>
  <div class="worker-dashboard-page">
    <main class="dashboard-main">
      <section class="dashboard-hero">
        <div class="hero-copy">
          <p class="hero-eyebrow">Worker overview</p>
          <h1>Salam, {{ displayName }}</h1>
          <p class="hero-subtext">{{ cityLabel }} · {{ workerTrackLabel }}</p>
        </div>

        <NuxtLink to="/shifts/log" class="header-action">
          <span>Log a shift</span>
          <span class="icon action-icon">north_east</span>
        </NuxtLink>
      </section>

      <section class="summary-grid" v-if="!summaryLoading">
        <article class="summary-card">
          <div class="card-label">Net (all shifts)</div>
          <div class="card-value">Rs {{ formatMoney(totalNetAllShifts) }}</div>
          <p class="card-helper">This month: Rs {{ formatMoney(summary?.this_month) }}</p>
        </article>

        <article class="summary-card">
          <div class="card-label">Effective hourly</div>
          <div class="card-value">
            Rs {{ formatMoney(effectiveHourly) }}<span class="card-suffix">/hr</span>
          </div>

          <p class="card-helper" v-if="hourlyDeltaPct !== null">
            City median
            <span :class="hourlyDeltaClass">{{ formatSignedPercent(hourlyDeltaPct) }}</span>
            (Rs {{ formatMoney(cityMedian?.median_hourly) }}/hr)
          </p>
          <p class="card-helper" v-else>City median unavailable</p>
        </article>

        <article class="summary-card">
          <div class="card-label">Avg commission (all shifts)</div>
          <div class="card-value">{{ formatPercent(avgCommissionLast30) }}%</div>
          <p class="card-helper">Across all platforms</p>
        </article>

        <article class="summary-card">
          <div class="card-label">Verified shifts</div>
          <div class="card-value">
            {{ verifiedShiftCount }}<span class="card-suffix">/{{ totalShiftCount }}</span>
          </div>
          <p class="card-helper"><span class="icon icon-inline">shield</span> earnings</p>
        </article>
      </section>

      <section class="summary-grid" v-else>
        <article class="summary-card skeleton-card" v-for="n in 4" :key="n"></article>
      </section>

      <section class="chart-card">
        <div class="chart-header">
          <h2>Weekly net earnings</h2>
          <p>Real shift data for the last 30 days</p>
        </div>

        <div v-if="loading && !shifts.length" class="chart-state">Loading weekly trend...</div>
        <div v-else-if="!hasWeeklyData" class="chart-state">
          No shifts in the last 30 days yet. Log a shift to start your earnings trendline.
        </div>

        <div v-else class="chart-shell">
          <svg
            class="earnings-chart"
            viewBox="0 0 760 310"
            role="img"
            aria-labelledby="weekly-net-title weekly-net-desc"
          >
            <title id="weekly-net-title">Weekly net earnings line chart</title>
            <desc id="weekly-net-desc">Net earnings grouped by week over the last 30 days.</desc>

            <defs>
              <linearGradient id="weeklyAreaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="var(--fg-primary)" stop-opacity="0.32" />
                <stop offset="100%" stop-color="var(--fg-primary)" stop-opacity="0.04" />
              </linearGradient>
            </defs>

            <g class="y-grid">
              <template v-for="tick in chartTicks" :key="`tick-${tick.value}`">
                <line :x1="chartDims.left" :x2="chartDims.right" :y1="tick.y" :y2="tick.y" />
                <text :x="chartDims.left - 12" :y="tick.y + 4">{{ formatAxisMoney(tick.value) }}</text>
              </template>
            </g>

            <path v-if="chartAreaPath" :d="chartAreaPath" class="chart-area" />
            <path v-if="chartLinePath" :d="chartLinePath" class="chart-line" />

            <g class="chart-points">
              <g v-for="(point, index) in chartPoints" :key="point.key">
                <circle
                  class="chart-point-hit"
                  :cx="point.x"
                  :cy="point.y"
                  r="12"
                  tabindex="0"
                  @mouseenter="setActivePoint(index)"
                  @focus="setActivePoint(index)"
                />
                <circle class="chart-point" :cx="point.x" :cy="point.y" r="4.5" />
              </g>
            </g>

            <g class="x-axis">
              <text
                v-for="point in chartPoints"
                :key="`label-${point.key}`"
                :x="point.x"
                :y="chartDims.bottom + 26"
              >
                {{ point.label }}
              </text>
            </g>
          </svg>

          <div
            v-if="activePoint"
            class="chart-tooltip"
            :style="{ left: `${activePoint.xPercent}%`, top: `${activePoint.yPercent}%` }"
          >
            <strong>{{ activePoint.label }}</strong>
            <span>Rs {{ formatMoney(activePoint.value) }}</span>
          </div>
        </div>
      </section>

      <p v-if="summaryError" class="table-empty">{{ summaryError }}</p>

      <!-- City Median Comparison -->
      <section class="comparison-card" v-if="summary">
        <div class="comparison-header">
          <h2>City Comparison</h2>
          <button
            class="ghost-btn"
            type="button"
            :disabled="!latestPlatform || loading"
            @click="refreshCityMedian"
          >
            Refresh
          </button>
        </div>

        <div v-if="cityMedian?.median_hourly" class="comparison-content">
          <p>City median hourly: <strong>PKR {{ formatMoney(cityMedian.median_hourly) }}</strong></p>
          <p>Your avg hourly: <strong>PKR {{ formatMoney(summary.avg_hourly) }}</strong></p>

          <div
            :class="[
              'comparison-status',
              Number(summary.avg_hourly || 0) >= Number(cityMedian.median_hourly || 0)
                ? 'above'
                : 'below'
            ]"
          >
            {{
              Number(summary.avg_hourly || 0) >= Number(cityMedian.median_hourly || 0)
                ? 'Above city median ✓'
                : 'Below city median — keep tracking trends'
            }}
          </div>
        </div>

        <p v-else class="comparison-empty">Not enough city data yet for this platform.</p>
      </section>

      <section class="anomaly-card">
        <div class="comparison-header">
          <h2>Anomaly Watch</h2>
          <button class="ghost-btn" type="button" :disabled="anomalyLoading" @click="runAnomalyScan">
            {{ anomalyLoading ? 'Scanning...' : 'Rescan' }}
          </button>
        </div>

        <p v-if="anomalyLoading" class="comparison-empty">Checking your recent shifts for unusual patterns...</p>
        <p v-else-if="anomalyError" class="comparison-empty">{{ anomalyError }}</p>
        <p v-else-if="!anomalies.length" class="comparison-empty">
          No anomalies detected in recent shifts.
        </p>

        <div v-else class="anomaly-list">
          <article
            v-for="(item, idx) in anomalies.slice(0, 5)"
            :key="`${item.date || 'unknown'}-${item.type || 'type'}-${idx}`"
            class="anomaly-item"
          >
            <div class="anomaly-top">
              <strong>{{ anomalyLabel(item.type) }}</strong>
              <span :class="['severity-pill', severityClass(item.severity)]">
                {{ String(item.severity || 'medium') }}
              </span>
            </div>
            <p class="anomaly-meta">
              {{ item.date || 'Unknown date' }} • {{ item.platform || 'Unknown platform' }}
              <template v-if="item.value !== undefined && item.value !== null">
                • Value: {{ item.value }}
              </template>
            </p>
            <p class="anomaly-explanation">{{ item.explanation || 'No explanation available.' }}</p>
          </article>
        </div>

        <p v-if="anomalyScannedAt" class="comparison-empty">
          Last scan: {{ formatScanTime(anomalyScannedAt) }}
        </p>
      </section>

      <!-- Recent Shifts -->
      <section class="table-card">
        <div class="table-header">
          <h2>Recent Shifts</h2>
          <NuxtLink to="/shifts" class="table-link">View all</NuxtLink>
        </div>

        <div v-if="loading" class="table-loading">Loading shifts...</div>

        <div v-else-if="shiftsError" class="table-empty">{{ shiftsError }}</div>

        <div v-else-if="!shifts.length" class="table-empty">
          No shifts logged yet. Start by creating your first shift entry.
        </div>

        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Platform</th>
                <th>Gross</th>
                <th>Net</th>
                <th>Commission</th>
                <th>Verification</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in shifts.slice(0, 10)" :key="s.id">
                <td>{{ s.shift_date }}</td>
                <td>{{ s.platform }}</td>
                <td>PKR {{ formatMoney(s.gross_earned) }}</td>
                <td>PKR {{ formatMoney(s.net_received) }}</td>
                <td>{{ commissionPct(s) }}%</td>
                <td>
                  <span :class="['status-pill', normalizeStatus(s.verification_status)]">
                    {{ s.verification_status || 'unverified' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Quick Links -->
      <section class="quick-links">
        <NuxtLink to="/shifts/log" class="quick-link-card">
          <span class="icon">add_circle</span>
          <div>
            <h3>Log a Shift</h3>
            <p>Add new earnings and deductions.</p>
          </div>
        </NuxtLink>

        <NuxtLink to="/grievances/new" class="quick-link-card">
          <span class="icon">campaign</span>
          <div>
            <h3>Post Grievance</h3>
            <p>Report issues and raise platform concerns.</p>
          </div>
        </NuxtLink>

        <NuxtLink to="/certificate" class="quick-link-card">
          <span class="icon">description</span>
          <div>
            <h3>Income Certificate</h3>
            <p>Generate and print verified earnings report.</p>
          </div>
        </NuxtLink>
      </section>
    </main>

    <div class="support-fab">
      <button type="button">
        <span class="icon">help_outline</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' as any })

import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useShiftsStore } from '../../stores/shifts'

type ShiftLike = {
  shift_date?: string | null
  net_received?: number | string | null
  hours_worked?: number | string | null
  gross_earned?: number | string | null
  platform_deductions?: number | string | null
  verification_status?: string | null
  platform?: string | null
}

type NormalizedShift = {
  date: Date
  netReceived: number
  grossEarned: number
  platformDeductions: number
  hoursWorked: number
  verificationStatus: string
  platform: string
}

type WeeklyBucket = {
  key: string
  label: string
  value: number
}

type ChartPoint = WeeklyBucket & {
  x: number
  y: number
}

const chartDims = {
  width: 760,
  height: 310,
  left: 64,
  right: 732,
  top: 24,
  bottom: 258,
} as const

const shiftsStore = useShiftsStore()
const supabase = useSupabaseClient()
const {
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
} = storeToRefs(shiftsStore)

const anomalyLoading = ref(false)
const sessionUser = ref<any>(null)
const activePointIndex = ref<number | null>(null)

const latestPlatform = computed(() =>
  String((shifts.value?.[0] as ShiftLike | undefined)?.platform || '').trim()
)

const startOfDay = (value: Date) => {
  const d = new Date(value)
  d.setHours(0, 0, 0, 0)
  return d
}

const addDays = (value: Date, days: number) => {
  const d = new Date(value)
  d.setDate(d.getDate() + days)
  return d
}

const startOfWeek = (value: Date) => {
  const d = startOfDay(value)
  const mondayOffset = (d.getDay() + 6) % 7
  d.setDate(d.getDate() - mondayOffset)
  return d
}

const toDateKey = (value: Date) => {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const parseShiftDate = (value: string | null | undefined) => {
  const text = String(value || '').trim()
  if (!text) return null

  const d = new Date(`${text}T12:00:00`)
  if (Number.isNaN(d.getTime())) return null
  d.setHours(0, 0, 0, 0)
  return d
}

const currentRange = computed(() => {
  const end = startOfDay(new Date())
  const start = addDays(end, -29)
  return { start, end }
})

const previousRange = computed(() => {
  const end = addDays(currentRange.value.start, -1)
  const start = addDays(end, -29)
  return { start, end }
})

const normalizeStatus = (status?: string | null) => {
  const v = String(status || 'unverified')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '_')

  if (v === 'verified') return 'verified'
  if (v === 'pending' || v === 'in_review' || v === 'under_review') return 'pending'
  if (v === 'flagged' || v === 'disputed' || v === 'unverifiable' || v === 'rejected') return 'flagged'
  return 'unverified'
}

const normalizedShifts = computed<NormalizedShift[]>(() => {
  return (shifts.value || [])
    .map((record) => {
      const shift = record as ShiftLike
      const date = parseShiftDate(shift.shift_date)
      if (!date) return null

      return {
        date,
        netReceived: Number(shift.net_received || 0),
        grossEarned: Number(shift.gross_earned || 0),
        platformDeductions: Number(shift.platform_deductions || 0),
        hoursWorked: Number(shift.hours_worked || 0),
        verificationStatus: String(shift.verification_status || ''),
        platform: String(shift.platform || ''),
      }
    })
    .filter((item): item is NormalizedShift => Boolean(item))
})

const totalNetAllShifts = computed(() => {
  return normalizedShifts.value.reduce((sum, shift) => sum + shift.netReceived, 0)
})

const totalShiftCount = computed(() => normalizedShifts.value.length)

const shiftsInLast30Days = computed(() => {
  const { start, end } = currentRange.value
  return normalizedShifts.value.filter((shift) => shift.date >= start && shift.date <= end)
})

const shiftsInPrior30Days = computed(() => {
  const { start, end } = previousRange.value
  return normalizedShifts.value.filter((shift) => shift.date >= start && shift.date <= end)
})

const netLast30Days = computed(() => {
  return shiftsInLast30Days.value.reduce((sum, shift) => sum + shift.netReceived, 0)
})

const netPrior30Days = computed(() => {
  return shiftsInPrior30Days.value.reduce((sum, shift) => sum + shift.netReceived, 0)
})

const netTrendPct = computed<number | null>(() => {
  if (netPrior30Days.value <= 0) return null
  return ((netLast30Days.value - netPrior30Days.value) / netPrior30Days.value) * 100
})

const netTrendClass = computed(() => {
  if (netTrendPct.value === null) return 'trend-neutral'
  return netTrendPct.value >= 0 ? 'trend-positive' : 'trend-negative'
})

const formatSignedPercent = (value: number) => {
  if (!Number.isFinite(value)) return '0.0%'
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
}

const netTrendText = computed(() => {
  if (netTrendPct.value === null) return 'No prior 30-day baseline'
  return `${formatSignedPercent(netTrendPct.value)} vs prior 30`
})

const effectiveHourly = computed(() => {
  const totals = normalizedShifts.value.reduce(
    (acc, shift) => {
      if (shift.hoursWorked > 0) {
        acc.hours += shift.hoursWorked
        acc.net += shift.netReceived
      }
      return acc
    },
    { net: 0, hours: 0 }
  )

  if (totals.hours > 0) {
    return totals.net / totals.hours
  }

  return Number(summary.value?.avg_hourly || 0)
})

const hourlyDeltaPct = computed<number | null>(() => {
  const median = Number(cityMedian.value?.median_hourly || 0)
  if (!Number.isFinite(median) || median <= 0) return null
  return ((effectiveHourly.value - median) / median) * 100
})

const hourlyDeltaClass = computed(() => {
  if (hourlyDeltaPct.value === null) return 'trend-neutral'
  return hourlyDeltaPct.value >= 0 ? 'delta-positive' : 'delta-negative'
})

const avgCommissionLast30 = computed(() => {
  const totals = normalizedShifts.value.reduce(
    (acc, shift) => {
      acc.gross += shift.grossEarned
      acc.deductions += shift.platformDeductions
      return acc
    },
    { gross: 0, deductions: 0 }
  )

  if (totals.gross > 0) {
    return (totals.deductions / totals.gross) * 100
  }

  return Number(summary.value?.avg_commission_pct || 0)
})

const verifiedShiftCount = computed(() => {
  return normalizedShifts.value.filter((shift) => normalizeStatus(shift.verificationStatus) === 'verified')
    .length
})

const inferCategoryFromPlatform = (platform: string) => {
  const value = String(platform || '').toLowerCase().trim()
  if (!value) return 'Gig Worker'

  const rideHailing = ['careem', 'indrive', 'uber', 'bykea', 'yango']
  const delivery = ['foodpanda', 'cheetay', 'delivery', 'courier']

  if (rideHailing.some((name) => value.includes(name))) return 'Ride Hailing'
  if (delivery.some((name) => value.includes(name))) return 'Delivery'
  return 'Gig Worker'
}

const workerTrackLabel = computed(() => {
  const metadataCategory = String(sessionUser.value?.user_metadata?.platform_category || '')
    .trim()
    .toLowerCase()

  if (metadataCategory === 'transport') return 'Ride Hailing'
  if (metadataCategory === 'delivery') return 'Delivery'
  if (metadataCategory === 'courier') return 'Courier'
  if (metadataCategory === 'other') return 'Other Gig Work'

  return inferCategoryFromPlatform(latestPlatform.value)
})

const cityLabel = computed(() => {
  const metadataCity = String(sessionUser.value?.user_metadata?.city_zone || '').trim()
  return metadataCity || 'City zone pending'
})

const displayName = computed(() => {
  const fullName = String(
    sessionUser.value?.user_metadata?.full_name || sessionUser.value?.user_metadata?.name || ''
  ).trim()

  if (fullName) {
    return fullName.split(/\s+/)[0]
  }

  const email = String(sessionUser.value?.email || '').trim()
  if (email.includes('@')) {
    return email.split('@')[0]
  }

  return 'Worker'
})

const formatWeekLabel = (value: Date) => {
  return value.toLocaleDateString('en-PK', { day: '2-digit', month: 'short' })
}

const weeklySeries = computed<WeeklyBucket[]>(() => {
  const { start, end } = currentRange.value
  const firstWeek = startOfWeek(start)
  const lastWeek = startOfWeek(end)

  const totalsByWeek = new Map<string, number>()
  for (const shift of shiftsInLast30Days.value) {
    const key = toDateKey(startOfWeek(shift.date))
    totalsByWeek.set(key, (totalsByWeek.get(key) || 0) + shift.netReceived)
  }

  const buckets: WeeklyBucket[] = []
  for (let cursor = new Date(firstWeek); cursor.getTime() <= lastWeek.getTime(); cursor = addDays(cursor, 7)) {
    const key = toDateKey(cursor)
    buckets.push({
      key,
      label: formatWeekLabel(cursor),
      value: Number(totalsByWeek.get(key) || 0),
    })
  }

  return buckets
})

const hasWeeklyData = computed(() => shiftsInLast30Days.value.length > 0)

const niceCeil = (value: number) => {
  if (!Number.isFinite(value) || value <= 0) return 1000
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)))
  const normalized = value / magnitude

  if (normalized <= 1) return magnitude
  if (normalized <= 2) return 2 * magnitude
  if (normalized <= 5) return 5 * magnitude
  return 10 * magnitude
}

const chartCeiling = computed(() => {
  const max = Math.max(...weeklySeries.value.map((point) => point.value), 0)
  if (max <= 0) return 1000
  return niceCeil(max * 1.15)
})

const chartTicks = computed(() => {
  const steps = 4
  const plotHeight = chartDims.bottom - chartDims.top

  return Array.from({ length: steps + 1 }, (_, index) => {
    const ratio = index / steps
    return {
      value: chartCeiling.value * (1 - ratio),
      y: chartDims.top + plotHeight * ratio,
    }
  })
})

const chartPoints = computed<ChartPoint[]>(() => {
  if (!weeklySeries.value.length) return []

  const plotWidth = chartDims.right - chartDims.left
  const plotHeight = chartDims.bottom - chartDims.top

  return weeklySeries.value.map((point, index) => {
    const x =
      weeklySeries.value.length === 1
        ? (chartDims.left + chartDims.right) / 2
        : chartDims.left + (plotWidth * index) / (weeklySeries.value.length - 1)
    const y = chartDims.bottom - (Math.max(point.value, 0) / chartCeiling.value) * plotHeight

    return {
      ...point,
      x,
      y,
    }
  })
})

const chartLinePath = computed(() => {
  if (!chartPoints.value.length) return ''
  return chartPoints.value
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
    .join(' ')
})

const chartAreaPath = computed(() => {
  if (!chartPoints.value.length) return ''

  const first = chartPoints.value[0]
  const last = chartPoints.value[chartPoints.value.length - 1]
  const pathBody = chartPoints.value.map((point) => `L ${point.x} ${point.y}`).join(' ')

  return `M ${first.x} ${chartDims.bottom} ${pathBody} L ${last.x} ${chartDims.bottom} Z`
})

watch(
  chartPoints,
  (points) => {
    activePointIndex.value = points.length ? points.length - 1 : null
  },
  { immediate: true }
)

const activePoint = computed(() => {
  if (!chartPoints.value.length) return null

  const safeIndex =
    activePointIndex.value === null
      ? chartPoints.value.length - 1
      : Math.min(Math.max(activePointIndex.value, 0), chartPoints.value.length - 1)

  const point = chartPoints.value[safeIndex]
  return {
    ...point,
    xPercent: (point.x / chartDims.width) * 100,
    yPercent: (point.y / chartDims.height) * 100,
  }
})

const setActivePoint = (index: number) => {
  activePointIndex.value = index
}

const formatMoney = (n: number | string | null | undefined) => {
  const num = Number(n || 0)
  if (!Number.isFinite(num)) return '0'
  return Math.round(num).toLocaleString('en-PK')
}

const formatPercent = (n: number | string | null | undefined) => {
  const num = Number(n || 0)
  if (!Number.isFinite(num)) return '0.0'
  return num.toFixed(1)
}

const formatAxisMoney = (n: number) => {
  const num = Number(n || 0)
  if (!Number.isFinite(num) || num <= 0) return '0k'

  const inThousands = num / 1000
  const precision = inThousands >= 10 ? 0 : 1
  return `${inThousands.toFixed(precision).replace(/\.0$/, '')}k`
}

const commissionPct = (s: any) => {
  const gross = Number(s?.gross_earned || 0)
  const ded = Number(s?.platform_deductions || 0)
  if (!gross) return '0.0'
  return ((ded / gross) * 100).toFixed(1)
}

const refreshCityMedian = async () => {
  if (!latestPlatform.value) return
  await shiftsStore.fetchCityMedian(latestPlatform.value)
}

const anomalyLabel = (value: string) => {
  return String(value || 'anomaly').replace(/_/g, ' ')
}

const severityClass = (value: string) => {
  const v = String(value || 'medium').toLowerCase()
  if (v.includes('critical')) return 'critical'
  if (v.includes('high')) return 'high'
  if (v.includes('medium')) return 'medium'
  return 'low'
}

const formatScanTime = (value: string | null | undefined) => {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('en-PK', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const runAnomalyScan = async () => {
  if (anomalyLoading.value) return
  anomalyLoading.value = true
  try {
    await shiftsStore.detectAnomalies()
  } finally {
    anomalyLoading.value = false
  }
}

const hydrateSessionUser = async () => {
  const { data } = await supabase.auth.getSession()
  sessionUser.value = data.session?.user || null
}

onMounted(async () => {
  await Promise.allSettled([shiftsStore.fetchShifts(), shiftsStore.fetchSummary(), hydrateSessionUser()])

  if (latestPlatform.value) {
    await shiftsStore.fetchCityMedian(latestPlatform.value).catch(() => null)
  }

  await runAnomalyScan()
})
</script>

<style scoped>
.worker-dashboard-page {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
}

.dashboard-main {
  max-width: 1080px;
  margin: 0 auto;
  display: grid;
  gap: 1.25rem;
}

.dashboard-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.hero-copy h1 {
  font-size: clamp(1.9rem, 3.7vw, 2.45rem);
  font-weight: 800;
  letter-spacing: -0.025em;
}

.hero-eyebrow {
  text-transform: uppercase;
  color: color-mix(in srgb, var(--fg-primary) 72%, var(--fg-muted));
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.hero-subtext {
  margin-top: 0.35rem;
  color: var(--fg-muted);
  font-weight: 600;
}

.header-action {
  min-height: 2.65rem;
  padding: 0.3rem 1rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;

  background-color: var(--fg-primary);
  color: #f2f1ff;
  text-decoration: none;
  border: 1px solid transparent;
  border-radius: 9999px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;

  transition:
    border-radius 0ms linear,
    background-color 120ms linear,
    color 120ms linear,
    border-color 120ms linear,
    box-shadow 140ms ease;

  box-shadow: var(--fg-shadow);
}

.action-icon {
  font-size: 1rem;
  transition: transform 140ms ease;
}

.header-action:hover {
  border-radius: 1rem;
  background: var(--fg-surface);
  color: var(--fg-primary);
  border-color: var(--fg-border);
  box-shadow: var(--fg-shadow);
}

.header-action:hover .action-icon {
  transform: translate(1px, -1px);
}

.header-action:active {
  filter: none;
}

.header-action:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 25%, transparent);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 0.9rem;
}

.summary-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1.05rem 1.15rem;
  min-height: 7.7rem;
  box-shadow: var(--fg-shadow);
}

.card-label {
  color: var(--fg-muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  font-weight: 700;
}

.card-value {
  margin-top: 0.52rem;
  font-size: clamp(1.8rem, 3vw, 2.2rem);
  font-weight: 800;
  line-height: 1.08;
}

.card-suffix {
  margin-left: 0.2rem;
  color: var(--fg-muted);
  font-size: 1rem;
  font-weight: 700;
}

.card-helper {
  margin-top: 0.64rem;
  color: var(--fg-muted);
  font-size: 0.84rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.card-helper.trend-positive {
  color: var(--fg-success);
}

.card-helper.trend-negative {
  color: #b54708;
}

.card-helper.trend-neutral {
  color: var(--fg-muted);
}

.delta-positive {
  color: var(--fg-success);
  font-weight: 800;
}

.delta-negative {
  color: #b54708;
  font-weight: 800;
}

.icon-inline {
  font-size: 0.92rem;
}

.skeleton-card {
  min-height: 7.7rem;
  background: linear-gradient(
    110deg,
    var(--fg-surface-muted) 8%,
    color-mix(in srgb, var(--fg-surface) 75%, var(--fg-surface-muted)) 18%,
    var(--fg-surface-muted) 33%
  );
  background-size: 200% 100%;
  animation: shine 1.2s linear infinite;
}
@keyframes shine {
  to {
    background-position-x: -200%;
  }
}

.chart-card,
.comparison-card,
.table-card,
.anomaly-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--fg-shadow);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 0.75rem;
}

.chart-header h2 {
  font-size: 1.18rem;
  font-weight: 800;
}

.chart-header p {
  color: var(--fg-muted);
  font-size: 0.84rem;
  font-weight: 600;
}

.chart-state {
  margin-top: 0.85rem;
  color: var(--fg-muted);
  font-size: 0.92rem;
}

.chart-shell {
  margin-top: 0.85rem;
  position: relative;
  border: 1px solid var(--fg-border);
  border-radius: 0.95rem;
  padding: 0.75rem 0.75rem 0.38rem;
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--fg-primary) 4%, var(--fg-surface)) 0%,
      var(--fg-surface) 45%
    );
}

.earnings-chart {
  width: 100%;
  height: clamp(230px, 34vw, 330px);
  display: block;
}

.y-grid line {
  stroke: color-mix(in srgb, var(--fg-muted) 18%, transparent);
  stroke-dasharray: 5 4;
}

.y-grid text {
  fill: var(--fg-muted);
  font-size: 10.5px;
  font-weight: 700;
  text-anchor: end;
}

.x-axis text {
  fill: var(--fg-muted);
  font-size: 12px;
  font-weight: 700;
  text-anchor: middle;
}

.chart-area {
  fill: url(#weeklyAreaGradient);
}

.chart-line {
  fill: none;
  stroke: var(--fg-primary);
  stroke-width: 2.8;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.chart-point {
  fill: var(--fg-surface);
  stroke: var(--fg-primary);
  stroke-width: 2.4;
}

.chart-point-hit {
  fill: transparent;
  cursor: pointer;
  outline: none;
}

.chart-point-hit:focus-visible {
  stroke: color-mix(in srgb, var(--fg-primary) 42%, transparent);
  stroke-width: 2;
}

.chart-tooltip {
  position: absolute;
  transform: translate(-50%, -110%);
  border: 1px solid var(--fg-border);
  border-radius: 0.7rem;
  padding: 0.4rem 0.6rem;
  box-shadow: var(--fg-shadow);
  background: var(--fg-surface);
  pointer-events: none;
  min-width: 6.1rem;
}

.chart-tooltip strong {
  color: var(--fg-muted);
  text-transform: uppercase;
  letter-spacing: 0.035em;
  font-size: 0.67rem;
  display: block;
}

.chart-tooltip span {
  color: var(--fg-text);
  font-size: 0.88rem;
  font-weight: 800;
}

.comparison-header,
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.comparison-header h2,
.table-header h2 {
  font-size: 1.1rem;
  font-weight: 800;
}

/* Secondary button polish + hover */
.ghost-btn,
.table-link {
  border: 1px solid var(--fg-border);
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  border-radius: 9999px;
  padding: 0.45rem 0.8rem;
  font-size: 0.8rem;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition:
    background-color 140ms ease,
    color 140ms ease,
    box-shadow 140ms ease,
    transform 140ms ease,
    border-color 140ms ease;
}

.ghost-btn:hover:not(:disabled),
.table-link:hover {
  background: color-mix(in srgb, var(--fg-primary) 12%, var(--fg-surface));
  border-color: color-mix(in srgb, var(--fg-primary) 35%, var(--fg-border));
  transform: translateY(-1px);
  box-shadow: 0 10px 18px -12px color-mix(in srgb, var(--fg-primary) 45%, transparent);
}

/* City Comparison refresh: button itself turns blue on hover */
.comparison-card .ghost-btn:hover:not(:disabled) {
  background: var(--fg-primary);
  border-color: var(--fg-primary);
  color: #f2f1ff;
  transform: translateY(-1px);
  box-shadow: 0 12px 22px -16px color-mix(in srgb, var(--fg-primary) 60%, transparent);
}

/* Anomaly Watch rescan: button itself turns blue on hover */
.anomaly-card .ghost-btn:hover:not(:disabled) {
  background: var(--fg-primary);
  border-color: var(--fg-primary);
  color: #f2f1ff;
  transform: translateY(-1px);
  box-shadow: 0 12px 22px -16px color-mix(in srgb, var(--fg-primary) 60%, transparent);
}

/* Recent Shifts: View all button itself turns blue on hover */
.table-card .table-link:hover {
  background: var(--fg-primary);
  border-color: var(--fg-primary);
  color: #f2f1ff;
  transform: translateY(-1px);
  box-shadow: 0 12px 22px -16px color-mix(in srgb, var(--fg-primary) 60%, transparent);
}

.ghost-btn:active:not(:disabled),
.table-link:active {
  transform: translateY(0);
}

.ghost-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.ghost-btn:focus-visible,
.table-link:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}

.comparison-content p {
  margin-top: 0.7rem;
  color: var(--fg-muted);
}

.comparison-status {
  margin-top: 0.85rem;
  display: inline-flex;
  border-radius: 9999px;
  padding: 0.45rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 700;
}

.comparison-status.above {
  background: color-mix(in srgb, var(--fg-success) 14%, var(--fg-surface));
  color: var(--fg-success);
}
.comparison-status.below {
  background: color-mix(in srgb, var(--fg-danger) 14%, var(--fg-surface));
  color: var(--fg-danger);
}
.comparison-empty {
  margin-top: 0.7rem;
  color: var(--fg-muted);
}

.anomaly-list {
  margin-top: 0.8rem;
  display: grid;
  gap: 0.7rem;
}

.anomaly-item {
  border: 1px solid var(--fg-border);
  border-radius: 0.85rem;
  padding: 0.75rem;
  background: var(--fg-surface-muted);
}

.anomaly-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
}

.anomaly-top strong {
  text-transform: capitalize;
  font-size: 0.92rem;
}

.severity-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  padding: 0.2rem 0.55rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: capitalize;
}

.severity-pill.critical {
  background: #ffe6e6;
  color: #b42318;
}

.severity-pill.high {
  background: #ffeed9;
  color: #b54708;
}

.severity-pill.medium {
  background: #fff6df;
  color: #8a5b00;
}

.severity-pill.low {
  background: var(--fg-surface-muted);
  color: var(--fg-muted);
}

.anomaly-meta {
  margin-top: 0.4rem;
  color: var(--fg-muted);
  font-size: 0.82rem;
}

.anomaly-explanation {
  margin-top: 0.35rem;
  line-height: 1.45;
  font-size: 0.84rem;
}

.table-loading,
.table-empty {
  margin-top: 0.8rem;
  color: var(--fg-muted);
  font-size: 0.92rem;
}

.table-wrap {
  margin-top: 0.8rem;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

th,
td {
  text-align: left;
  padding: 0.75rem 0.5rem;
  border-bottom: 1px solid var(--fg-border);
  font-size: 0.88rem;
}

th {
  color: var(--fg-muted);
  font-weight: 700;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.22rem 0.58rem;
  border-radius: 9999px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: capitalize;
}

.status-pill.verified {
  background: color-mix(in srgb, var(--fg-success) 14%, var(--fg-surface));
  color: var(--fg-success);
}
.status-pill.pending {
  background: #fff6df;
  color: #8a5b00;
}
.status-pill.flagged {
  background: #ffe9e9;
  color: #8a1f1f;
}
.status-pill.unverified {
  background: var(--fg-surface-muted);
  color: var(--fg-muted);
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 0.8rem;
}

/* Clickable cards with hover lift/glow */
.quick-link-card {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  text-decoration: none;
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  color: var(--fg-text);
  box-shadow: var(--fg-shadow);
  transition:
    transform 170ms cubic-bezier(0.2, 0.8, 0.2, 1),
    box-shadow 170ms ease,
    border-color 140ms ease,
    background-color 140ms ease;
}

.quick-link-card .icon {
  color: var(--fg-primary);
  transition: transform 170ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
.quick-link-card h3 {
  font-size: 1rem;
  font-weight: 800;
}
.quick-link-card p {
  margin-top: 0.25rem;
  color: var(--fg-muted);
  font-size: 0.85rem;
}

.quick-link-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, #fff 35%, var(--fg-primary));
  background: var(--fg-primary);
  color: #f2f1ff;
  box-shadow: 0 16px 28px -18px color-mix(in srgb, var(--fg-primary) 55%, transparent);
}

.quick-link-card:hover .icon {
  color: #f2f1ff;
  transform: scale(1.08);
}

.quick-link-card:hover p {
  color: color-mix(in srgb, #fff 78%, transparent);
}

.quick-link-card:active {
  transform: translateY(-1px);
}

.quick-link-card:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}

.support-fab {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 50;
}
.support-fab button {
  width: 3.5rem;
  height: 3.5rem;
  background-color: var(--fg-surface);
  box-shadow: var(--fg-shadow);
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fg-primary);
  border: 1px solid var(--fg-border);
  cursor: pointer;
  transition: all 0.3s;
}

.support-fab button:hover {
  background-color: var(--fg-primary);
  color: #f2f1ff;
}

.support-fab .icon {
  font-size: 1.5rem;
  transition: transform 0.3s;
}

.support-fab button:hover .icon {
  transform: scale(1.1);
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .header-action,
  .ghost-btn,
  .table-link,
  .quick-link-card,
  .quick-link-card .icon,
  .support-fab button,
  .support-fab .icon {
    transition: none !important;
  }
}

/* Responsive */
@media (max-width: 679px) {
  .dashboard-hero {
    flex-direction: column;
    align-items: stretch;
  }

  .header-action {
    width: 100%;
    max-width: none;
  }

  .hero-copy h1 {
    font-size: 1.78rem;
  }

  .summary-card {
    padding: 0.85rem;
  }

  .chart-shell {
    padding: 0.55rem 0.45rem 0.2rem;
  }

  .chart-tooltip {
    min-width: 5.6rem;
    padding: 0.36rem 0.52rem;
  }
}

@media (min-width: 680px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .quick-links {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .summary-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .quick-links {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .header-action {
    width: 100%;
  }
}

/* Material Symbols Outlined */
.icon {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  direction: ltr;
  font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}
</style> 