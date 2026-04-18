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
        </div>

        <div v-if="loading" class="panel-state">Loading flags...</div>
        <div v-else-if="!kpis?.vulnerability_flags?.length" class="panel-state">
          No vulnerability flags found in current data.
        </div>

        <div v-else class="flag-list">
          <article class="flag-card" v-for="flag in kpis.vulnerability_flags" :key="flag.worker_id">
            <div class="flag-top">
              <strong>Worker {{ shortId(flag.worker_id) }}</strong>
              <span class="drop-pill">↓ {{ flag.drop_pct }}%</span>
            </div>
            <p>This month: PKR {{ formatNum(flag.this_month) }}</p>
            <p>Last month: PKR {{ formatNum(flag.last_month) }}</p>
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
                <th>Platform</th>
                <th>Month</th>
                <th>Avg Commission %</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in kpis.commission_trends" :key="`${t.platform}-${t.month}`">
                <td>{{ t.platform }}</td>
                <td>{{ formatMonth(t.month) }}</td>
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
              <p>Avg Net: <strong>PKR {{ formatNum(zone.avg_net) }}</strong></p>
              <p>Workers: <strong>{{ zone.workers }}</strong></p>
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
              :key="`${c.category}-${c.platform}`"
            >
              <span class="platform">{{ c.platform }}</span>
              <span class="category">{{ c.category }}</span>
              <span class="count">{{ c.count }} reports</span>
            </article>
          </div>
        </div>
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

import { ref } from 'vue'
import { useApi } from '../../composables/useApi'

const { authFetch } = useApi()

const loading = ref(false)
const kpis = ref<any>(null)

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

const formatMonth = (d: string) =>
  new Date(d).toLocaleDateString('en-PK', { month: 'short', year: 'numeric' })

const loadKpis = async () => {
  loading.value = true
  try {
    kpis.value = await authFetch('/analytics/kpis')
  } finally {
    loading.value = false
  }
}

await loadKpis()
</script>

<style scoped>
.advocate-dashboard-page {
  min-height: 100vh;
  background: #f5f7f9;
  color: #2c2f31;
  font-family: 'Raleway', sans-serif;
  padding: 2rem;
}

.dashboard-main {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  gap: 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
.page-header h1 {
  font-size: 2rem;
  font-weight: 800;
}
.page-header p {
  margin-top: 0.35rem;
  color: #595c5e;
}
.header-action {
  border: none;
  border-radius: 9999px;
  background: #0545ef;
  color: #f2f1ff;
  font-weight: 700;
  padding: 0.7rem 1rem;
  cursor: pointer;
}
.header-action:disabled {
  background: #595c5e;
  cursor: not-allowed;
}

.kpi-grid {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}
.kpi-card {
  background: #ffffff;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 12px 24px -16px rgba(44, 47, 49, 0.18);
}
.card-label {
  color: #595c5e;
  font-size: 0.82rem;
  font-weight: 600;
}
.card-value {
  margin-top: 0.4rem;
  font-size: 1.35rem;
  font-weight: 800;
}

.panel-card {
  background: #ffffff;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 12px 24px -16px rgba(44, 47, 49, 0.18);
}
.panel-header h2 {
  font-size: 1.05rem;
  font-weight: 800;
}
.panel-state {
  margin-top: 0.75rem;
  color: #595c5e;
}

.flag-list {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.75rem;
}
.flag-card {
  border: 1px solid #eef1f3;
  border-radius: 0.9rem;
  padding: 0.85rem;
  background: #fbfcfd;
}
.flag-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.drop-pill {
  background: #ffe9e9;
  color: #8a1f1f;
  border-radius: 9999px;
  padding: 0.2rem 0.55rem;
  font-size: 0.75rem;
  font-weight: 700;
}
.flag-card p {
  margin-top: 0.35rem;
  color: #595c5e;
  font-size: 0.88rem;
}

.table-wrap {
  margin-top: 0.8rem;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  min-width: 620px;
}
th,
td {
  text-align: left;
  border-bottom: 1px solid #eef1f3;
  padding: 0.7rem 0.45rem;
  font-size: 0.87rem;
}
th {
  color: #595c5e;
  font-weight: 700;
}
.high {
  color: #d92d20;
  font-weight: 800;
}

.split-panels {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.zone-grid {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.7rem;
}
.zone-card {
  border: 1px solid #eef1f3;
  border-radius: 0.9rem;
  padding: 0.85rem;
  background: #fbfcfd;
}
.zone-card h3 {
  font-size: 0.95rem;
  font-weight: 800;
}
.zone-card p {
  margin-top: 0.35rem;
  color: #595c5e;
  font-size: 0.86rem;
}

.complaint-list {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.55rem;
}
.complaint-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 0.5rem;
  align-items: center;
  border: 1px solid #eef1f3;
  border-radius: 0.8rem;
  padding: 0.6rem 0.7rem;
}
.platform {
  font-weight: 700;
}
.category {
  color: #595c5e;
  font-size: 0.88rem;
}
.count {
  background: #eef1f3;
  border-radius: 9999px;
  padding: 0.25rem 0.55rem;
  font-size: 0.75rem;
  font-weight: 700;
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
  background: #fff;
  border: none;
  border-radius: 9999px;
  color: #0545ef;
  box-shadow: 0 24px 24px -4px rgba(44, 47, 49, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
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