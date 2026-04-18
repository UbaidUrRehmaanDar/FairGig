<template>
  <div class="certificate-page">
    <main class="certificate-main">
      <!-- Controls -->
      <section class="controls-card no-print">
        <div class="controls-header">
          <div>
            <h1>Income Certificate</h1>
            <p>Generate a verified earnings certificate for a selected date range.</p>
          </div>
          <NuxtLink to="/dashboard/worker" class="back-link">Back to Dashboard</NuxtLink>
        </div>

        <div class="filters-grid">
          <div class="input-group">
            <label for="start-date">Start Date</label>
            <div class="input-with-icon">
              <span class="icon">calendar_month</span>
              <input id="start-date" v-model="startDate" type="date" />
            </div>
          </div>

          <div class="input-group">
            <label for="end-date">End Date</label>
            <div class="input-with-icon">
              <span class="icon">event</span>
              <input id="end-date" v-model="endDate" type="date" />
            </div>
          </div>
        </div>

        <p v-if="message" :class="['form-message', messageType]">{{ message }}</p>

        <div class="actions">
          <button type="button" class="primary-button" :disabled="loading" @click="generate">
            <span v-if="!loading">Generate Certificate</span>
            <span v-else>Generating...</span>
          </button>

          <button
            type="button"
            class="ghost-button"
            :disabled="!certData"
            @click="printCertificate"
          >
            Print / Save PDF
          </button>
        </div>
      </section>

      <!-- Printable Certificate -->
      <section v-if="certData" class="certificate-card" id="certificate">
        <div class="cert-header">
          <h2>FairGig</h2>
          <p>Verified Income Certificate</p>
        </div>

        <div class="cert-body">
          <p class="intro">
            This certifies that <strong>{{ certData.worker?.full_name || 'N/A' }}</strong>,
            a worker in <strong>{{ certData.worker?.city_zone || 'N/A' }}</strong>,
            has the following verified earnings for the selected period:
          </p>

          <p class="period">
            Period:
            <strong>{{ certData.period?.start }}</strong>
            to
            <strong>{{ certData.period?.end }}</strong>
          </p>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Platform</th>
                  <th>Gross (PKR)</th>
                  <th>Net (PKR)</th>
                  <th>Hours</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in certData.shifts || []" :key="s.id">
                  <td>{{ s.shift_date }}</td>
                  <td>{{ s.platform }}</td>
                  <td>{{ formatNum(s.gross_earned) }}</td>
                  <td>{{ formatNum(s.net_received) }}</td>
                  <td>{{ s.hours_worked ?? '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="summary-grid">
            <article class="summary-box">
              <span>Total Verified Earnings</span>
              <strong>PKR {{ formatNum(certData.summary?.total_net) }}</strong>
            </article>
            <article class="summary-box">
              <span>Total Shifts</span>
              <strong>{{ certData.summary?.total_shifts ?? 0 }}</strong>
            </article>
            <article class="summary-box">
              <span>Total Hours</span>
              <strong>{{ certData.summary?.total_hours?.toFixed?.(1) || '—' }}</strong>
            </article>
          </div>

          <p class="note">
            All earnings listed are verified through FairGig screenshot review workflows.
          </p>
        </div>

        <div class="cert-footer">
          <span>Generated: {{ todayLabel }}</span>
          <span>FairGig — Empowering Gig Workers</span>
        </div>
      </section>
    </main>

    <div class="support-fab no-print">
      <button type="button">
        <span class="icon">help_outline</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' as any, layout: 'print' })

import { computed, ref } from 'vue'
import { useApi } from '../composables/useApi'

const { authFetch } = useApi()

const startDate = ref('')
const endDate = ref('')
const loading = ref(false)

const message = ref('')
const messageType = ref<'error' | 'success'>('success')

const certData = ref<any>(null)

const todayLabel = computed(() =>
  new Date().toLocaleDateString('en-PK', { year: 'numeric', month: 'short', day: 'numeric' })
)

const formatNum = (n: number | string | null | undefined) => {
  const num = Number(n || 0)
  if (!Number.isFinite(num)) return '—'
  return Math.round(num).toLocaleString('en-PK')
}

const validate = () => {
  if (!startDate.value || !endDate.value) {
    messageType.value = 'error'
    message.value = 'Please select both start and end dates.'
    return false
  }
  if (startDate.value > endDate.value) {
    messageType.value = 'error'
    message.value = 'Start date cannot be after end date.'
    return false
  }
  return true
}

const generate = async () => {
  if (loading.value) return
  message.value = ''

  if (!validate()) return

  loading.value = true
  try {
    certData.value = await authFetch(
      `/certificates/data?start_date=${startDate.value}&end_date=${endDate.value}`
    )

    messageType.value = 'success'
    message.value = 'Certificate generated successfully.'
  } catch (e: any) {
    messageType.value = 'error'
    message.value = e?.message || 'Failed to generate certificate.'
  } finally {
    loading.value = false
  }
}

const printCertificate = () => {
  window.print()
}
</script>

<style scoped>
.certificate-page {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
  padding: 2rem;
}
.certificate-main {
  max-width: 980px;
  margin: 0 auto;
  display: grid;
  gap: 1rem;
}

.controls-card,
.certificate-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--fg-shadow);
}

.controls-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
.controls-header h1 {
  font-size: 2rem;
  font-weight: 800;
}
.controls-header p {
  margin-top: 0.35rem;
  color: var(--fg-muted);
}
.back-link {
  text-decoration: none;
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  border-radius: 9999px;
  padding: 0.65rem 0.9rem;
  font-size: 0.85rem;
  font-weight: 700;
}

.filters-grid {
  margin-top: 0.9rem;
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
.input-with-icon input {
  width: 100%;
  border: none;
  border-radius: 1rem;
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  outline: none;
  font-family: inherit;
  padding: 0.88rem 1rem 0.88rem 2.7rem;
}
.input-with-icon input:focus {
  background: var(--fg-surface);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}

.form-message {
  margin-top: 0.75rem;
  font-size: 0.84rem;
  font-weight: 700;
}
.form-message.success {
  color: var(--fg-success);
}
.form-message.error {
  color: var(--fg-danger);
}

.actions {
  margin-top: 0.85rem;
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
}
.primary-button,
.ghost-button {
  border: none;
  border-radius: 9999px;
  padding: 0.65rem 1rem;
  font-weight: 700;
  cursor: pointer;
}
.primary-button {
  background: var(--fg-primary);
  color: #f2f1ff;
}
.primary-button:disabled {
  background: var(--fg-muted);
  cursor: not-allowed;
}
.ghost-button {
  background: var(--fg-surface-muted);
  color: var(--fg-text);
}
.ghost-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.cert-header {
  text-align: center;
  border-bottom: 1px solid var(--fg-border);
  padding-bottom: 0.9rem;
}
.cert-header h2 {
  font-size: 2rem;
  font-weight: 800;
  color: var(--fg-primary);
}
.cert-header p {
  margin-top: 0.2rem;
  color: var(--fg-muted);
  font-weight: 600;
}

.cert-body {
  margin-top: 1rem;
}
.intro {
  line-height: 1.55;
}
.period {
  margin-top: 0.7rem;
  color: var(--fg-muted);
}

.table-wrap {
  margin-top: 0.9rem;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  min-width: 620px;
}
th,
td {
  border: 1px solid var(--fg-border);
  padding: 0.62rem 0.5rem;
  font-size: 0.86rem;
  text-align: left;
}
th {
  background: var(--fg-surface-muted);
  font-weight: 700;
  color: var(--fg-muted);
}

.summary-grid {
  margin-top: 0.95rem;
  display: grid;
  gap: 0.65rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}
.summary-box {
  border: 1px solid var(--fg-border);
  border-radius: 0.8rem;
  padding: 0.72rem;
  background: var(--fg-surface-muted);
}
.summary-box span {
  display: block;
  color: var(--fg-muted);
  font-size: 0.8rem;
}
.summary-box strong {
  margin-top: 0.25rem;
  display: block;
  font-size: 1rem;
  font-weight: 800;
}

.note {
  margin-top: 0.95rem;
  font-size: 0.84rem;
  color: var(--fg-muted);
}
.cert-footer {
  margin-top: 1rem;
  padding-top: 0.7rem;
  border-top: 1px solid var(--fg-border);
  display: flex;
  justify-content: space-between;
  gap: 0.7rem;
  font-size: 0.8rem;
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

@media (min-width: 820px) {
  .filters-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

/* print behavior */
@media print {
  .no-print {
    display: none !important;
  }
  .certificate-page {
    background: #fff;
    padding: 0;
  }
  .certificate-main {
    max-width: 100%;
  }
  .certificate-card {
    box-shadow: none;
    border-radius: 0;
    padding: 0;
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