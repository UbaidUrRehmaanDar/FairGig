<template>
  <div class="worker-dashboard-page">
    <main class="dashboard-main">
      <div class="page-header">
        <div>
          <h1>Worker Dashboard</h1>
          <p>Track your earnings, verification status, and quick actions.</p>
        </div>
        <NuxtLink to="/shifts/log" class="header-action">+ Log Shift</NuxtLink>
      </div>

      <!-- Summary Cards -->
      <section class="summary-grid" v-if="summary">
        <article class="summary-card">
          <div class="card-label">This Month</div>
          <div class="card-value">PKR {{ formatNum(summary.this_month) }}</div>
        </article>

        <article class="summary-card">
          <div class="card-label">This Week</div>
          <div class="card-value">PKR {{ formatNum(summary.this_week) }}</div>
        </article>

        <article class="summary-card">
          <div class="card-label">Avg Hourly</div>
          <div class="card-value">PKR {{ formatNum(summary.avg_hourly) }}/hr</div>
        </article>

        <article class="summary-card">
          <div class="card-label">Platform Takes</div>
          <div class="card-value highlight">{{ formatNum(summary.avg_commission_pct) }}%</div>
        </article>
      </section>

      <section class="summary-grid" v-else>
        <article class="summary-card skeleton-card" v-for="n in 4" :key="n"></article>
      </section>

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
          <p>City median hourly: <strong>PKR {{ formatNum(cityMedian.median_hourly) }}</strong></p>
          <p>Your avg hourly: <strong>PKR {{ formatNum(summary.avg_hourly) }}</strong></p>

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

      <!-- Recent Shifts -->
      <section class="table-card">
        <div class="table-header">
          <h2>Recent Shifts</h2>
          <NuxtLink to="/shifts" class="table-link">View all</NuxtLink>
        </div>

        <div v-if="loading" class="table-loading">Loading shifts...</div>

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
                <td>PKR {{ formatNum(s.gross_earned) }}</td>
                <td>PKR {{ formatNum(s.net_received) }}</td>
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

import { computed, onMounted, ref } from 'vue'
import { useShiftsStore } from '../../stores/shifts'

const shiftsStore = useShiftsStore()
const shifts = ref<any[]>([])
const summary = ref<any>(null)
const cityMedian = ref<any>(null)
const loading = ref(false)

const latestPlatform = computed(() => String(shifts.value?.[0]?.platform || ''))

const formatNum = (n: number | string | null | undefined) => {
  const num = Number(n || 0)
  if (!Number.isFinite(num) || num === 0) return '—'
  return Math.round(num).toLocaleString('en-PK')
}

const commissionPct = (s: any) => {
  const gross = Number(s?.gross_earned || 0)
  const ded = Number(s?.platform_deductions || 0)
  if (!gross) return '0.0'
  return ((ded / gross) * 100).toFixed(1)
}

const normalizeStatus = (status: string) => {
  const v = String(status || 'unverified').toLowerCase()
  if (v.includes('verified')) return 'verified'
  if (v.includes('pending')) return 'pending'
  if (v.includes('flag')) return 'flagged'
  if (v.includes('unverifiable')) return 'flagged'
  return 'unverified'
}

const refreshCityMedian = async () => {
  if (!latestPlatform.value) return
  cityMedian.value = await shiftsStore.fetchCityMedian()
}

onMounted(async () => {
  loading.value = true
  try {
    shifts.value = await shiftsStore.fetchShifts()
    summary.value = await shiftsStore.fetchSummary()
    if (latestPlatform.value) {
      cityMedian.value = await shiftsStore.fetchCityMedian()
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.worker-dashboard-page {
  min-height: 100vh;
  background: #f5f7f9;
  color: #2c2f31;
  font-family: 'Raleway', sans-serif;
  padding: 2rem;
}

.dashboard-main {
  max-width: 1080px;
  margin: 0 auto;
  display: grid;
  gap: 1.25rem;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.025em;
}

.page-header p {
  margin-top: 0.35rem;
  color: #595c5e;
}

.header-action {
  background: #0545ef;
  color: #f2f1ff;
  text-decoration: none;
  padding: 0.7rem 1rem;
  border-radius: 9999px;
  font-weight: 700;
  font-size: 0.9rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 0.9rem;
}

.summary-card {
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
  margin-top: 0.45rem;
  font-size: 1.35rem;
  font-weight: 800;
}

.card-value.highlight {
  color: #0545ef;
}

.skeleton-card {
  min-height: 82px;
  background: linear-gradient(110deg, #eef1f3 8%, #f8f9fa 18%, #eef1f3 33%);
  background-size: 200% 100%;
  animation: shine 1.2s linear infinite;
}
@keyframes shine {
  to {
    background-position-x: -200%;
  }
}

.comparison-card,
.table-card {
  background: #ffffff;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 12px 24px -16px rgba(44, 47, 49, 0.18);
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

.ghost-btn,
.table-link {
  border: none;
  background: #eef1f3;
  color: #2c2f31;
  border-radius: 9999px;
  padding: 0.45rem 0.8rem;
  font-size: 0.8rem;
  font-weight: 700;
  text-decoration: none;
}

.comparison-content p {
  margin-top: 0.7rem;
  color: #595c5e;
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
  background: #e8f8ef;
  color: #0b7a33;
}
.comparison-status.below {
  background: #fff6f6;
  color: #d92d20;
}
.comparison-empty {
  margin-top: 0.7rem;
  color: #595c5e;
}

.table-loading,
.table-empty {
  margin-top: 0.8rem;
  color: #595c5e;
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
  border-bottom: 1px solid #eef1f3;
  font-size: 0.88rem;
}

th {
  color: #595c5e;
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
  background: #e7f8ef;
  color: #0b7a33;
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
  background: #eef1f3;
  color: #595c5e;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 0.8rem;
}

.quick-link-card {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  text-decoration: none;
  background: #ffffff;
  border-radius: 1rem;
  padding: 1rem;
  color: #2c2f31;
  box-shadow: 0 12px 24px -16px rgba(44, 47, 49, 0.18);
}

.quick-link-card .icon {
  color: #0545ef;
}
.quick-link-card h3 {
  font-size: 1rem;
  font-weight: 800;
}
.quick-link-card p {
  margin-top: 0.25rem;
  color: #595c5e;
  font-size: 0.85rem;
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
  background-color: #ffffff;
  box-shadow: 0 24px 24px -4px rgba(44, 47, 49, 0.12);
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0545ef;
  border: none;
  cursor: pointer;
}

/* Responsive */
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