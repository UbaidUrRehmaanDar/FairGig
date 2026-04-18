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
      <section class="summary-grid" v-if="!summaryLoading && summary">
        <article class="summary-card">
          <div class="card-label">This Month</div>
          <div class="card-value">PKR {{ formatMoney(summary.this_month) }}</div>
        </article>

        <article class="summary-card">
          <div class="card-label">This Week</div>
          <div class="card-value">PKR {{ formatMoney(summary.this_week) }}</div>
        </article>

        <article class="summary-card">
          <div class="card-label">Avg Hourly</div>
          <div class="card-value">PKR {{ formatMoney(summary.avg_hourly) }}/hr</div>
        </article>

        <article class="summary-card">
          <div class="card-label">Platform Takes</div>
          <div class="card-value highlight">{{ formatPercent(summary.avg_commission_pct) }}%</div>
        </article>

        <article class="summary-card">
          <div class="card-label">Total Shifts</div>
          <div class="card-value">{{ formatCount(summary.total_shifts) }}</div>
        </article>
      </section>

      <section class="summary-grid" v-else>
        <article class="summary-card skeleton-card" v-for="n in 5" :key="n"></article>
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

import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useShiftsStore } from '../../stores/shifts'

const shiftsStore = useShiftsStore()
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
  anomalyScannedAt
} = storeToRefs(shiftsStore)
const anomalyLoading = ref(false)

const latestPlatform = computed(() => String(shifts.value?.[0]?.platform || ''))

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

const formatCount = (n: number | string | null | undefined) => {
  const num = Number(n || 0)
  if (!Number.isFinite(num)) return '0'
  return Math.round(num).toLocaleString('en-PK')
}

const commissionPct = (s: any) => {
  const gross = Number(s?.gross_earned || 0)
  const ded = Number(s?.platform_deductions || 0)
  if (!gross) return '0.0'
  return ((ded / gross) * 100).toFixed(1)
}

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
    minute: '2-digit'
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

onMounted(async () => {
  await Promise.allSettled([shiftsStore.fetchShifts(), shiftsStore.fetchSummary()])

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
  color: var(--fg-muted);
}

/* Primary CTA with your bounce morphology */
.header-action {
  width: 18rem;
  height: 3.2rem;
  padding: 0 1.25rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;

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

.header-action:hover {
  border-radius: 1rem;
  background: var(--fg-surface);
  color: var(--fg-primary);
  border-color: var(--fg-border);
  box-shadow: var(--fg-shadow);
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
  padding: 1rem;
  box-shadow: var(--fg-shadow);
}

.card-label {
  color: var(--fg-muted);
  font-size: 0.82rem;
  font-weight: 600;
}

.card-value {
  margin-top: 0.45rem;
  font-size: 1.35rem;
  font-weight: 800;
}

.card-value.highlight {
  color: var(--fg-primary);
}

.skeleton-card {
  min-height: 82px;
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

.comparison-card,
.table-card,
.anomaly-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--fg-shadow);
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
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  .header-action {
    width: 100%;
    max-width: none;
  }
  .page-header h1 {
    font-size: 1.75rem;
  }
  .summary-card {
    padding: 0.85rem;
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
    width: min(18rem, 92vw);
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