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
definePageMeta({ middleware: 'auth' as any })

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
  border-radius: 1.25rem;
  padding: 1.25rem;
  box-shadow: var(--fg-shadow);
}

.controls-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
.controls-header h1 {
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.controls-header p {
  margin-top: 0.35rem;
  color: var(--fg-muted);
  font-size: 0.95rem;
}
.back-link {
  text-decoration: none;
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  border-radius: 9999px;
  padding: 0.6rem 1rem;
  font-size: 0.85rem;
  font-weight: 700;
  transition: all 0.2s ease;
}
.back-link:hover {
  background: var(--fg-border);
  transform: translateY(-1px);
}

.filters-grid {
  margin-top: 1.25rem;
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}
.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.input-group label {
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--fg-muted);
  margin-left: 0.25rem;
}
.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-icon .icon {
  position: absolute;
  left: 0.9rem;
  color: var(--fg-muted);
  font-size: 1.25rem;
  pointer-events: none;
}
.input-with-icon input {
  width: 100%;
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  outline: none;
  font-family: inherit;
  padding: 0.75rem 1rem 0.75rem 2.85rem;
  transition: all 0.2s ease;
}
.input-with-icon input:focus {
  background: var(--fg-surface);
  border-color: var(--fg-primary);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--fg-primary) 10%, transparent);
}

.form-message {
  margin-top: 1rem;
  font-size: 0.88rem;
  font-weight: 700;
  padding: 0.75rem;
  border-radius: 0.75rem;
}
.form-message.success {
  background: color-mix(in srgb, var(--fg-success) 10%, transparent);
  color: var(--fg-success);
}
.form-message.error {
  background: color-mix(in srgb, var(--fg-danger) 10%, transparent);
  color: var(--fg-danger);
}

.actions {
  margin-top: 1.25rem;
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.primary-button,
.ghost-button {
  height: 3.25rem;
  border-radius: 9999px;
  padding: 0 1.5rem;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.primary-button {
  border: 1px solid transparent;
  background: var(--fg-primary);
  color: #f2f1ff;
  box-shadow: var(--fg-shadow);

  transition:
    border-radius 0ms linear,
    background-color 120ms linear,
    color 120ms linear,
    border-color 120ms linear,
    box-shadow 140ms ease;
}

.primary-button:hover:not(:disabled) {
  border-radius: 1rem;
  background: var(--fg-surface);
  color: var(--fg-primary);
  border-color: var(--fg-border);
  box-shadow: var(--fg-shadow);
}

.primary-button:active:not(:disabled) {
  filter: none;
}

.primary-button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 25%, transparent);
}

.primary-button:disabled {
  background: var(--fg-muted);
  color: #f2f1ff;
  border-color: transparent;
  cursor: not-allowed;
  opacity: 0.7;
}

/* Ghost = muted default, stronger white-ish surface hover */
.ghost-button {
  border: 1px solid var(--fg-border);
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  box-shadow: var(--fg-shadow);

  transition:
    border-radius 0ms linear,
    background-color 120ms linear,
    color 120ms linear,
    border-color 120ms linear,
    box-shadow 140ms ease;
}

.ghost-button:hover:not(:disabled) {
  border-radius: 1rem;
  background: var(--fg-surface);
  color: var(--fg-primary);
  border-color: var(--fg-border);
  box-shadow: var(--fg-shadow);
}

.ghost-button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}

.ghost-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}


.cert-header {
  text-align: center;
  border-bottom: 2px solid var(--fg-border);
  padding-bottom: 1.5rem;
}
.cert-header h2 {
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--fg-primary);
  letter-spacing: -0.04em;
}
.cert-header p {
  margin-top: 0.35rem;
  color: var(--fg-muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 0.85rem;
}

.cert-body {
  margin-top: 1.5rem;
}
.intro {
  line-height: 1.6;
  font-size: 1.1rem;
}
.period {
  margin-top: 1rem;
  color: var(--fg-muted);
  font-weight: 600;
}

.table-wrap {
  margin-top: 1.5rem;
  overflow-x: auto;
  border-radius: 1rem;
  border: 1px solid var(--fg-border);
}
table {
  width: 100%;
  border-collapse: collapse;
  min-width: 650px;
}
th,
td {
  padding: 1rem;
  font-size: 0.9rem;
  text-align: left;
  border-bottom: 1px solid var(--fg-border);
}
th {
  background: var(--fg-surface-muted);
  font-weight: 800;
  color: var(--fg-text);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}

.summary-grid {
  margin-top: 1.5rem;
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}
.summary-box {
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1.25rem;
  background: var(--fg-surface-muted);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.summary-box span {
  color: var(--fg-muted);
  font-size: 0.85rem;
  font-weight: 600;
}
.summary-box strong {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--fg-text);
}

.note {
  margin-top: 1.5rem;
  font-size: 0.9rem;
  color: var(--fg-muted);
  font-style: italic;
  line-height: 1.5;
}
.cert-footer {
  margin-top: 2rem;
  padding-top: 1.25rem;
  border-top: 2px solid var(--fg-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--fg-muted);
  font-weight: 600;
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
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.support-fab button:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
}

@media (min-width: 820px) {
  .filters-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .controls-header {
    flex-direction: column;
    align-items: stretch;
  }
  .back-link {
    text-align: center;
    margin-top: 0.5rem;
  }
  .actions button {
    width: 100%;
  }
  .cert-header h2 {
    font-size: 1.75rem;
  }
  .intro {
    font-size: 0.95rem;
  }
  .cert-footer {
    flex-direction: column;
    text-align: center;
  }
}

/* print behavior */
@media print {
  :global(.no-print) {
    display: none !important;
  }
  :global(.iphone-nav) {
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
    border: none;
  }
  table {
    min-width: 100%;
  }
}
</style>