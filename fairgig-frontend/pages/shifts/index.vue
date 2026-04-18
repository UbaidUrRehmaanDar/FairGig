<template>
  <div class="shifts-history-page">
    <main class="history-main">
      <div class="page-header">
        <div>
          <h1>Shift History</h1>
          <p>Review all logged shifts and their verification status.</p>
        </div>
        <NuxtLink to="/shifts/log" class="header-action">+ Log New Shift</NuxtLink>
      </div>

      <section class="filters-card">
        <div class="filters-grid">
          <div class="input-group">
            <label for="platform-filter">Platform</label>
            <div class="input-with-icon">
              <span class="icon">filter_alt</span>
              <select id="platform-filter" v-model="platformFilter">
                <option value="">All Platforms</option>
                <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
          </div>

          <div class="input-group">
            <label for="status-filter">Verification Status</label>
            <div class="input-with-icon">
              <span class="icon">rule</span>
              <select id="status-filter" v-model="statusFilter">
                <option value="">All Statuses</option>
                <option value="verified">Verified</option>
                <option value="pending">Pending</option>
                <option value="flagged">Flagged</option>
                <option value="unverified">Unverified</option>
              </select>
            </div>
          </div>

          <div class="input-group">
            <label for="search-filter">Search Notes/Platform</label>
            <div class="input-with-icon">
              <span class="icon">search</span>
              <input id="search-filter" v-model.trim="searchText" type="text" placeholder="Type to search..." />
            </div>
          </div>
        </div>
      </section>

      <section class="table-card">
        <div class="table-header">
          <h2>All Shifts</h2>
          <span class="count-pill">{{ filteredShifts.length }} records</span>
        </div>

        <div v-if="loading" class="table-state">Loading shifts...</div>
        <div v-else-if="!filteredShifts.length" class="table-state">No shifts match your filters.</div>

        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Platform</th>
                <th>Hours</th>
                <th>Gross (PKR)</th>
                <th>Deductions (PKR)</th>
                <th>Net (PKR)</th>
                <th>Commission</th>
                <th>Status</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="shift in filteredShifts" :key="shift.id">
                <td>{{ shift.shift_date }}</td>
                <td>{{ shift.platform }}</td>
                <td>{{ shift.hours_worked ?? '—' }}</td>
                <td>{{ formatNum(shift.gross_earned) }}</td>
                <td>{{ formatNum(shift.platform_deductions) }}</td>
                <td>{{ formatNum(shift.net_received) }}</td>
                <td>{{ commissionPct(shift) }}%</td>
                <td>
                  <span :class="['status-pill', normalizeStatus(shift.verification_status)]">
                    {{ shift.verification_status || 'unverified' }}
                  </span>
                </td>
                <td class="note-cell">{{ shift.notes || '—' }}</td>
              </tr>
            </tbody>
          </table>
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

import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useShiftsStore } from '../../stores/shifts'

const shiftsStore = useShiftsStore()
const { shifts, loading } = storeToRefs(shiftsStore)

const platformFilter = ref('')
const statusFilter = ref('')
const searchText = ref('')

const platforms = computed(() => {
  const set = new Set<string>()
  for (const s of shifts.value || []) {
    if (s?.platform) set.add(String(s.platform))
  }
  return Array.from(set).sort()
})

const normalizeStatus = (status: string) => {
  const v = String(status || 'unverified').toLowerCase()
  if (v.includes('verified')) return 'verified'
  if (v.includes('pending')) return 'pending'
  if (v.includes('flag')) return 'flagged'
  if (v.includes('unverifiable')) return 'flagged'
  return 'unverified'
}

const commissionPct = (s: any) => {
  const gross = Number(s?.gross_earned || 0)
  const ded = Number(s?.platform_deductions || 0)
  if (!gross) return '0.0'
  return ((ded / gross) * 100).toFixed(1)
}

const formatNum = (n: number | string | null | undefined) => {
  const num = Number(n || 0)
  if (!Number.isFinite(num)) return '—'
  return Math.round(num).toLocaleString('en-PK')
}

const filteredShifts = computed(() => {
  const search = searchText.value.toLowerCase()
  return (shifts.value || []).filter((s: any) => {
    const status = normalizeStatus(s.verification_status)
    const platformOk = !platformFilter.value || s.platform === platformFilter.value
    const statusOk = !statusFilter.value || status === statusFilter.value
    const searchOk =
      !search ||
      String(s.platform || '').toLowerCase().includes(search) ||
      String(s.notes || '').toLowerCase().includes(search)
    return platformOk && statusOk && searchOk
  })
})

onMounted(async () => {
  await shiftsStore.fetchShifts()
})
</script>

<style scoped>
.shifts-history-page {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
  padding: 2rem;
}
.history-main {
  max-width: 1120px;
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
  color: var(--fg-muted);
}
.header-action {
  text-decoration: none;
  background: var(--fg-primary);
  color: #f2f1ff;
  border-radius: 9999px;
  padding: 0.7rem 1rem;
  font-weight: 700;
  font-size: 0.88rem;
}

.filters-card,
.table-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--fg-shadow);
}

.filters-grid {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}
.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}
.input-group label {
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--fg-muted);
  margin-left: 0.2rem;
}
.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-icon .icon {
  position: absolute;
  left: 0.85rem;
  color: var(--fg-muted);
  font-size: 1.2rem;
  pointer-events: none;
}
.input-with-icon input,
.input-with-icon select {
  width: 100%;
  border: none;
  border-radius: 1rem;
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  outline: none;
  font-family: inherit;
  padding: 0.88rem 1rem 0.88rem 2.7rem;
}
.input-with-icon input:focus,
.input-with-icon select:focus {
  background: var(--fg-surface);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.table-header h2 {
  font-size: 1.08rem;
  font-weight: 800;
}
.count-pill {
  background: var(--fg-surface-muted);
  border-radius: 9999px;
  padding: 0.3rem 0.65rem;
  font-size: 0.76rem;
  font-weight: 700;
}
.table-state {
  margin-top: 0.75rem;
  color: var(--fg-muted);
}

.table-wrap {
  margin-top: 0.75rem;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  min-width: 980px;
}
th,
td {
  text-align: left;
  border-bottom: 1px solid var(--fg-border);
  padding: 0.72rem 0.45rem;
  font-size: 0.86rem;
}
th {
  color: var(--fg-muted);
  font-weight: 700;
}
.note-cell {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.58rem;
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

.support-fab {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 50;
}
.support-fab button {
  width: 3.5rem;
  height: 3.5rem;
  border: 1px solid var(--fg-border);
  border-radius: 9999px;
  background: var(--fg-surface);
  color: var(--fg-primary);
  box-shadow: var(--fg-shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

@media (min-width: 900px) {
  .filters-grid {
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