<template>
  <div class="advocate-dashboard-page">
    <main class="dashboard-main">
      <div class="page-header">
        <div>
          <h1>Advocate Dashboard</h1>
          <p>Monitor platform-level trends, vulnerability flags, and grievance patterns.</p>
        </div>
        <button type="button" class="header-action" :disabled="loading" @click="loadKpis">
          {{ loading ? 'Refreshing...' : 'Refresh Analytics' }}
        </button>
      </div>

      <!-- KPI Cards -->
      <section class="kpi-grid">
        <article class="kpi-card">
          <div class="card-label">Vulnerability Flags</div>
          <div class="card-value">{{ kpis?.vulnerability_flags?.length || 0 }}</div>
        </article>

        <article class="kpi-card">
          <div class="card-label">Complaint Categories (7 days)</div>
          <div class="card-value">{{ kpis?.top_complaints?.length || 0 }}</div>
        </article>

        <article class="kpi-card">
          <div class="card-label">Zones Tracked</div>
          <div class="card-value">{{ kpis?.income_by_zone?.length || 0 }}</div>
        </article>
      </section>

      <!-- Vulnerability Flags -->
      <section class="panel-card">
        <div class="panel-header">
          <h2>⚠ Vulnerability Flags (Income Drop &gt; 20%)</h2>
          <button
            type="button"
            class="danger-action"
            :disabled="loading || deletingAllFlags || !kpis?.vulnerability_flags?.length"
            @click="deleteAllFlags"
          >
            {{ deletingAllFlags ? 'Deleting...' : 'Delete All Flags' }}
          </button>
        </div>

        <div v-if="loading" class="panel-state">Loading flags...</div>
        <div v-else-if="!kpis?.vulnerability_flags?.length" class="panel-state">
          No vulnerability flags found in current data.
        </div>

        <div v-else class="flag-list">
          <article
            class="flag-card"
            v-for="flag in kpis.vulnerability_flags"
            :key="`${flag.worker_id}-${flag.shift_date}-${flag.platform}`"
          >
            <div class="flag-top">
              <strong>{{ flag.full_name || `Worker ${shortId(flag.worker_id)}` }}</strong>
              <span class="drop-pill">↓ {{ formatPct(flag.income_drop_pct) }}%</span>
            </div>
            <p>{{ flag.city_zone || 'Unknown zone' }} • {{ flag.platform || 'Unknown platform' }}</p>
            <p>Shift date: {{ formatDate(flag.shift_date) }}</p>
            <p>Previous net: PKR {{ formatNum(flag.prev_net_received) }}</p>
            <p>Current net: PKR {{ formatNum(flag.net_received) }}</p>
            <button
              type="button"
              class="delete-flag-btn"
              :disabled="deletingFlagKey === flagKey(flag)"
              @click="deleteFlag(flag)"
            >
              {{ deletingFlagKey === flagKey(flag) ? 'Deleting...' : 'Delete Flag' }}
            </button>
          </article>
        </div>
      </section>

      <!-- Commission Trends -->
      <section class="panel-card">
        <div class="panel-header">
          <h2>Platform Commission Trends</h2>
        </div>

        <div v-if="loading" class="panel-state">Loading trends...</div>
        <div v-else-if="!kpis?.commission_trends?.length" class="panel-state">
          No commission trend data available.
        </div>

        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Shift Date</th>
                <th>Sample Size</th>
                <th>Avg Commission %</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in kpis.commission_trends" :key="t.shift_date">
                <td>{{ formatDate(t.shift_date) }}</td>
                <td>{{ Number(t.sample_size || 0) }}</td>
                <td :class="{ high: Number(t.avg_commission_pct) > 25 }">
                  {{ Number(t.avg_commission_pct || 0).toFixed(1) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Income by Zone + Top Complaints -->
      <section class="split-panels">
        <div class="panel-card">
          <div class="panel-header">
            <h2>Income by Zone</h2>
          </div>

          <div v-if="loading" class="panel-state">Loading zone data...</div>
          <div v-else-if="!kpis?.income_by_zone?.length" class="panel-state">No zone data available.</div>

          <div v-else class="zone-grid">
            <article class="zone-card" v-for="zone in kpis.income_by_zone" :key="zone.city_zone">
              <h3>{{ zone.city_zone }}</h3>
              <p>Total Net: <strong>PKR {{ formatNum(zone.total_net_received) }}</strong></p>
              <p>Avg Net: <strong>PKR {{ formatNum(zone.avg_net_received) }}</strong></p>
              <p>Workers: <strong>{{ Number(zone.worker_count || 0) }}</strong></p>
              <p>Samples: <strong>{{ Number(zone.sample_size || 0) }}</strong></p>
            </article>
          </div>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <h2>Top Complaints (7 days)</h2>
          </div>

          <div v-if="loading" class="panel-state">Loading complaints...</div>
          <div v-else-if="!kpis?.top_complaints?.length" class="panel-state">No complaints found.</div>

          <div v-else class="complaint-list">
            <article
              class="complaint-row"
              v-for="c in kpis.top_complaints"
              :key="c.category"
            >
              <span class="platform">{{ c.category }}</span>
              <span class="category">{{ Number(c.total_upvotes || 0) }} upvotes</span>
              <span class="count">{{ Number(c.total_count || 0) }} reports • {{ Number(c.total_upvotes || 0) }} upvotes</span>
            </article>
          </div>
        </div>
      </section>
    </main>

  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' as any })

import { onMounted, ref } from 'vue'

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

const { authFetch } = useApi()

const loading = ref(false)
const kpis = ref<AnalyticsKpis | null>(null)
const deletingAllFlags = ref(false)
const deletingFlagKey = ref('')

const shortId = (value?: string) => {
  const v = String(value || '')
  if (v.length <= 8) return v
  return `${v.slice(0, 8)}...`
}

const formatNum = (n: number | string | null | undefined) => {
  const num = Number(n || 0)
  if (!Number.isFinite(num) || num === 0) return '—'
  return Math.round(num).toLocaleString('en-PK')
}

const formatDate = (d: string) => {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-PK')
}

const formatPct = (n: number | string | null | undefined) => {
  const value = Number(n || 0)
  if (!Number.isFinite(value)) return '0.0'
  return value.toFixed(1)
}

const flagKey = (flag: AnalyticsKpis['vulnerability_flags'][number]) => {
  return `${flag.worker_id}-${flag.shift_date}-${flag.platform}`
}

const loadKpis = async () => {
  loading.value = true
  try {
    const data = await authFetch<Partial<AnalyticsKpis>>('/analytics/kpis')
    kpis.value = {
      commission_trends: Array.isArray(data?.commission_trends) ? data.commission_trends : [],
      income_by_zone: Array.isArray(data?.income_by_zone) ? data.income_by_zone : [],
      vulnerability_flags: Array.isArray(data?.vulnerability_flags) ? data.vulnerability_flags : [],
      top_complaints: Array.isArray(data?.top_complaints) ? data.top_complaints : []
    }
  } catch {
    kpis.value = null
  } finally {
    loading.value = false
  }
}

const deleteFlag = async (flag: AnalyticsKpis['vulnerability_flags'][number]) => {
  const confirmed = window.confirm('Delete this vulnerability flag from the database?')
  if (!confirmed) return

  const key = flagKey(flag)
  deletingFlagKey.value = key
  try {
    await authFetch('/analytics/vulnerability-flags', {
      method: 'DELETE',
      body: {
        worker_id: flag.worker_id,
        platform: flag.platform,
        shift_date: flag.shift_date,
      },
    })
    await loadKpis()
  } finally {
    deletingFlagKey.value = ''
  }
}

const deleteAllFlags = async () => {
  const confirmed = window.confirm('Delete ALL vulnerability flags from the database?')
  if (!confirmed) return

  deletingAllFlags.value = true
  try {
    await authFetch('/analytics/vulnerability-flags/all', { method: 'DELETE' })
    await loadKpis()
  } finally {
    deletingAllFlags.value = false
  }
}

onMounted(async () => {
  await loadKpis()
})
</script>

<style scoped>
.advocate-dashboard-page {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
}

.dashboard-main {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  gap: 1.25rem;
  min-width: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.25rem;
}

.page-header h1 {
  font-size: 1.85rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.page-header p {
  margin-top: 0.35rem;
  color: var(--fg-muted);
  font-size: 1rem;
  font-weight: 600;
}

.header-action {
  border: none;
  border-radius: 9999px;
  background: var(--fg-primary);
  color: #fff;
  font-weight: 800;
  padding: 0.75rem 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.header-action:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.1);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}

.header-action:disabled {
  background: var(--fg-muted);
  opacity: 0.7;
  cursor: not-allowed;
}

.kpi-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.kpi-card,
.panel-card {
  border: 1px solid var(--fg-border);
  border-radius: 1.25rem;
  padding: 1.25rem;
  box-shadow: var(--fg-shadow);
  min-width: 0;
  overflow: hidden;
  background: var(--fg-surface);
}

.card-label,
.panel-header h2 {
  font-weight: 800;
  letter-spacing: -0.01em;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.card-label {
  color: var(--fg-muted);
  font-size: 0.85rem;
  text-transform: uppercase;
}

.card-value {
  margin-top: 0.5rem;
  font-size: 1.9rem;
  font-weight: 900;
  line-height: 1;
}

.panel-header h2 {
  font-size: 1.15rem;
}

.danger-action,
.delete-flag-btn {
  border: 1px solid color-mix(in srgb, var(--fg-danger) 35%, transparent);
  background: color-mix(in srgb, var(--fg-danger) 10%, transparent);
  color: var(--fg-danger);
  font-weight: 800;
  border-radius: 9999px;
  cursor: pointer;
}

.danger-action {
  padding: 0.45rem 0.9rem;
  font-size: 0.8rem;
  white-space: nowrap;
}

.delete-flag-btn {
  margin-top: 0.75rem;
  padding: 0.4rem 0.85rem;
  font-size: 0.78rem;
}

.danger-action:disabled,
.delete-flag-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.panel-state {
  margin-top: 1rem;
  color: var(--fg-muted);
  font-weight: 600;
  text-align: center;
  padding: 2rem 0;
}

.flag-list,
.zone-grid,
.complaint-list {
  margin-top: 1rem;
  display: grid;
  gap: 1rem;
}

.flag-card,
.zone-card,
.complaint-row {
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  background: var(--fg-surface-muted);
}

.flag-card:hover {
  border-color: var(--fg-danger);
}

.flag-top,
.complaint-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.flag-top strong,
.zone-card h3,
.complaint-row .platform {
  font-weight: 800;
}

.drop-pill {
  background: color-mix(in srgb, var(--fg-danger) 10%, transparent);
  color: var(--fg-danger);
  border-radius: 9999px;
  padding: 0.25rem 0.65rem;
  font-size: 0.8rem;
  font-weight: 800;
}

.flag-card p,
.zone-card p,
.complaint-row .category {
  margin-top: 0.5rem;
  color: var(--fg-muted);
  font-size: 0.92rem;
  font-weight: 600;
}

.table-wrap {
  margin-top: 1rem;
  overflow-x: auto;
  border-radius: 1rem;
  border: 1px solid var(--fg-border);
  width: 100%;
  min-width: 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 500px;
}

th,
td {
  text-align: left;
  border-bottom: 1px solid var(--fg-border);
  padding: 1rem;
  font-size: 0.92rem;
}

th {
  background: var(--fg-surface-muted);
  color: var(--fg-muted);
  font-weight: 800;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}

.high {
  color: var(--fg-danger);
  font-weight: 900;
}

.split-panels {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.zone-card strong,
.complaint-row .count {
  color: var(--fg-text);
  font-weight: 800;
}

.complaint-row .category {
  flex: 1;
  min-width: 0;
  margin-top: 0;
}

.complaint-row .count {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 9999px;
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
  white-space: normal;
  overflow-wrap: anywhere;
  max-width: 100%;
}

@media (min-width: 700px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .zone-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .split-panels {
    grid-template-columns: 1.2fr 1fr;
  }
}

@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-action {
    width: 100%;
    margin-top: 0.5rem;
  }

  .card-value {
    font-size: 1.5rem;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .complaint-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.35rem;
  }

  .complaint-row .count {
    align-self: stretch;
    margin-top: 0.25rem;
  }
}
</style>