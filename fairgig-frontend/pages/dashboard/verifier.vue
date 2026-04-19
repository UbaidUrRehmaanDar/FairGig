<template>
  <div class="verify-page">
    <main class="verify-shell">
      <header class="verify-header">
        <p class="eyebrow">Verifier Queue</p>
        <div class="title-row">
          <div>
            <h1>Pending verifications</h1>
            <p>Review each submission against the screenshot. Confirm, flag, or mark unverifiable.</p>
          </div>
          <button
            type="button"
            class="refresh-btn"
            :disabled="isLoading || isRefreshing"
            @click="refreshQueue"
          >
            {{ isRefreshing ? 'Refreshing...' : 'Refresh queue' }}
          </button>
        </div>
      </header>

      <section class="stats-strip" aria-label="Queue summary">
        <article>
          <span>Pending</span>
          <strong>{{ queue.length }}</strong>
        </article>
        <article>
          <span>Reviewed (session)</span>
          <strong>{{ reviewedCount }}</strong>
        </article>
        <article>
          <span>Confirmed (session)</span>
          <strong>{{ verifiedCount }}</strong>
        </article>
      </section>

      <p v-if="flash" :class="['flash-message', flash.type]">{{ flash.text }}</p>

      <section v-if="isLoading" class="state-card">Loading pending verifications...</section>
      <section v-else-if="!queue.length" class="state-card">No pending verifications right now.</section>

      <section v-else class="verify-list">
        <article class="verify-card" v-for="item in queue" :key="item.id">
          <div class="verify-card-top">
            <div>
              <h2>{{ item.platform || 'Unknown platform' }} · {{ formatDate(item.shift_date) }}</h2>
              <p>
                {{ item.city_zone || 'Unknown city' }}
                · {{ item.full_name || 'worker' }} {{ shortId(item.worker_id) }}
              </p>
            </div>
            <div class="rate-block">
              <span>Effective Rate</span>
              <strong>{{ formatCurrency(effectiveRate(item)) }}/hr</strong>
            </div>
          </div>

          <div class="verify-card-body">
            <div class="details-column">
              <div class="metric-grid">
                <article class="metric-item">
                  <span>Hours</span>
                  <strong>{{ formatHours(item.hours_worked) }}</strong>
                </article>
                <article class="metric-item">
                  <span>Gross</span>
                  <strong>{{ formatCurrency(item.gross_earned) }}</strong>
                </article>
                <article class="metric-item">
                  <span>Deducted</span>
                  <strong>-{{ formatCurrency(item.platform_deductions) }}</strong>
                </article>
                <article class="metric-item">
                  <span>Net</span>
                  <strong>{{ formatCurrency(item.net_received) }}</strong>
                </article>
              </div>

              <p class="commission-copy">
                Implied commission rate: <strong>{{ impliedCommission(item) }}%</strong>
              </p>

              <label class="note-label" :for="`note-${item.id}`">
                Verifier note (optional, visible to the worker)
              </label>
              <textarea
                :id="`note-${item.id}`"
                v-model.trim="notes[item.id]"
                rows="3"
                maxlength="1200"
                placeholder="Add a note for the worker..."
              />
            </div>

            <div class="preview-column">
              <div class="preview-frame">
                <img
                  v-if="previewUrl(item)"
                  :src="previewUrl(item) || ''"
                  alt="Uploaded earnings screenshot"
                  loading="lazy"
                  @error="handlePreviewError(item.id)"
                />
                <div v-else class="preview-empty">
                  <span class="icon">image_not_supported</span>
                  <p>No screenshot uploaded</p>
                  <small>Mark as unverifiable</small>
                </div>
              </div>
            </div>
          </div>

          <footer class="verify-card-actions">
            <button
              type="button"
              class="action-btn neutral"
              :disabled="Boolean(busy[item.id])"
              @click="review(item, 'unverifiable')"
            >
              {{ busy[item.id] ? 'Saving...' : 'Unverifiable' }}
            </button>

            <button
              type="button"
              class="action-btn warning"
              :disabled="Boolean(busy[item.id])"
              @click="review(item, 'flagged')"
            >
              <span class="icon">outlined_flag</span>
              {{ busy[item.id] ? 'Saving...' : 'Flag discrepancy' }}
            </button>

            <button
              type="button"
              class="action-btn success"
              :disabled="Boolean(busy[item.id])"
              @click="review(item, 'verified')"
            >
              <span class="icon">shield</span>
              {{ busy[item.id] ? 'Saving...' : 'Confirm verified' }}
            </button>
          </footer>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' as any })

import { onMounted, reactive, ref } from 'vue'
import type { User } from '@supabase/supabase-js'
import { useApi } from '../../composables/useApi'

type ReviewStatus = 'verified' | 'flagged' | 'unverifiable'

type PendingVerification = {
  id: string
  shift_id: string
  worker_id: string
  storage_path: string | null
  status: string
  created_at: string
  platform: string
  shift_date: string
  hours_worked: number | null
  gross_earned: number
  platform_deductions: number
  net_received: number
  full_name: string | null
  city_zone: string | null
  signed_preview_url: string | null
}

const { authFetch } = useApi()
const supabase = useSupabaseClient()

const queue = ref<PendingVerification[]>([])
const isLoading = ref(true)
const isRefreshing = ref(false)
const reviewedCount = ref(0)
const verifiedCount = ref(0)

const notes = reactive<Record<string, string>>({})
const busy = reactive<Record<string, boolean>>({})
const previewOverrides = reactive<Record<string, string | null>>({})

const flash = ref<{ type: 'success' | 'error'; text: string } | null>(null)

const shortId = (value?: string) => {
  const safe = String(value || '')
  if (safe.length <= 8) return safe || '—'
  return `${safe.slice(0, 8)}...`
}

const toNumber = (value: unknown) => {
  const num = Number(value || 0)
  return Number.isFinite(num) ? num : 0
}

const formatDate = (value?: string) => {
  const safe = String(value || '').trim()
  if (!safe) return 'Unknown date'
  return safe
}

const formatCurrency = (value: unknown) => {
  return `Rs ${Math.round(toNumber(value)).toLocaleString('en-PK')}`
}

const formatHours = (value: number | null) => {
  if (value == null) return '—'
  return toNumber(value).toFixed(1)
}

const impliedCommission = (item: PendingVerification) => {
  const gross = toNumber(item.gross_earned)
  if (gross <= 0) return '0.0'
  const ratio = (toNumber(item.platform_deductions) / gross) * 100
  return ratio.toFixed(1)
}

const effectiveRate = (item: PendingVerification) => {
  const hours = toNumber(item.hours_worked)
  if (hours <= 0) return 0
  return toNumber(item.net_received) / hours
}

const previewUrl = (item: PendingVerification) => {
  if (previewOverrides[item.id]) return previewOverrides[item.id]
  if (item.signed_preview_url) return item.signed_preview_url
  return null
}

const resolveRole = (user: User | null) => {
  const fromUserMetadata =
    typeof user?.user_metadata?.role === 'string' ? user.user_metadata.role : ''
  const fromAppMetadata =
    typeof user?.app_metadata?.role === 'string' ? user.app_metadata.role : ''
  return String(fromUserMetadata || fromAppMetadata || 'worker').toLowerCase().trim()
}

const setFlash = (type: 'success' | 'error', text: string) => {
  flash.value = { type, text }
  if (!import.meta.client) return
  window.setTimeout(() => {
    if (flash.value?.text === text) {
      flash.value = null
    }
  }, 3200)
}

const normalizeItem = (raw: any): PendingVerification => {
  return {
    id: String(raw?.id || ''),
    shift_id: String(raw?.shift_id || ''),
    worker_id: String(raw?.worker_id || ''),
    storage_path: raw?.storage_path ? String(raw.storage_path) : null,
    status: String(raw?.status || 'pending'),
    created_at: String(raw?.created_at || ''),
    platform: String(raw?.platform || 'Unknown platform'),
    shift_date: String(raw?.shift_date || ''),
    hours_worked:
      raw?.hours_worked === null || raw?.hours_worked === undefined
        ? null
        : Number(raw.hours_worked),
    gross_earned: Number(raw?.gross_earned || 0),
    platform_deductions: Number(raw?.platform_deductions || 0),
    net_received: Number(raw?.net_received || 0),
    full_name: raw?.full_name ? String(raw.full_name) : null,
    city_zone: raw?.city_zone ? String(raw.city_zone) : null,
    signed_preview_url: raw?.signed_preview_url ? String(raw.signed_preview_url) : null,
  }
}

const ensureRoleAccess = async () => {
  const { data } = await supabase.auth.getSession()
  const sessionUser = data.session?.user || null

  if (!sessionUser) {
    await navigateTo('/login')
    return false
  }

  const role = resolveRole(sessionUser)
  if (role !== 'verifier' && role !== 'advocate') {
    await navigateTo(role === 'advocate' ? '/dashboard/advocate' : '/dashboard/worker')
    return false
  }

  return true
}

const fetchSignedPreview = async (item: PendingVerification) => {
  if (previewUrl(item)) return
  if (!item.storage_path) return

  try {
    const payload = await authFetch<{ signed_url?: string }>(
      `/screenshots/view/${item.id}?redirect=false`
    )
    const resolved = String(payload?.signed_url || '').trim()
    if (resolved) {
      previewOverrides[item.id] = resolved
    }
  } catch {
    previewOverrides[item.id] = null
  }
}

const loadPending = async (silent = false) => {
  if (!silent) {
    isLoading.value = true
  }

  try {
    const payload = await authFetch('/screenshots/pending')
    const rawItems = Array.isArray(payload) ? payload : []
    queue.value = rawItems.map(normalizeItem)

    await Promise.all(queue.value.map((item) => fetchSignedPreview(item)))
  } catch (error: any) {
    queue.value = []
    setFlash('error', error?.message || 'Failed to load pending verifications.')
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

const refreshQueue = async () => {
  isRefreshing.value = true
  await loadPending(true)
}

const handlePreviewError = (itemId: string) => {
  previewOverrides[itemId] = null
}

const review = async (item: PendingVerification, status: ReviewStatus) => {
  if (busy[item.id]) return

  busy[item.id] = true
  try {
    await authFetch(`/screenshots/${item.id}/review`, {
      method: 'PATCH',
      body: JSON.stringify({
        status,
        note: String(notes[item.id] || ''),
      }),
    })

    reviewedCount.value += 1
    if (status === 'verified') {
      verifiedCount.value += 1
    }

    queue.value = queue.value.filter((entry) => entry.id !== item.id)
    delete notes[item.id]
    delete previewOverrides[item.id]

    const successLabel =
      status === 'verified'
        ? 'Submission marked verified.'
        : status === 'flagged'
          ? 'Submission flagged for discrepancy.'
          : 'Submission marked as unverifiable.'
    setFlash('success', successLabel)
  } catch (error: any) {
    setFlash('error', error?.message || 'Failed to save verification review.')
  } finally {
    busy[item.id] = false
  }
}

onMounted(async () => {
  const allowed = await ensureRoleAccess()
  if (!allowed) return
  await loadPending()
})
</script>

<style scoped>
.verify-page {
  min-height: 100vh;
  padding: clamp(1rem, 3vw, 2.5rem);
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
  overflow-x: clip;
}

.verify-shell {
  width: 100%;
  max-width: 1140px;
  margin: 0 auto;
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.verify-header {
  display: grid;
  gap: 0.75rem;
}

.eyebrow {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: color-mix(in srgb, var(--fg-primary) 72%, var(--fg-muted));
}

.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.title-row h1 {
  margin: 0;
  font-size: clamp(1.65rem, 2.6vw, 2.3rem);
  letter-spacing: -0.03em;
}

.title-row p {
  margin: 0.4rem 0 0;
  color: var(--fg-muted);
  font-size: 1.05rem;
}

.refresh-btn {
  border: 1px solid var(--fg-border);
  background: var(--fg-surface);
  color: var(--fg-text);
  border-radius: 0.8rem;
  padding: 0.65rem 0.95rem;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: 160ms ease;
}

.refresh-btn:hover:not(:disabled) {
  border-color: color-mix(in srgb, var(--fg-primary) 30%, var(--fg-border));
  transform: translateY(-1px);
}

.refresh-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.stats-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.stats-strip article {
  border: 1px solid var(--fg-border);
  border-radius: 0.85rem;
  background: var(--fg-surface);
  padding: 0.75rem 0.9rem;
  display: grid;
  gap: 0.25rem;
}

.stats-strip span {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--fg-muted);
}

.stats-strip strong {
  font-size: 1.4rem;
  line-height: 1;
}

.flash-message {
  margin: 0;
  border-radius: 0.8rem;
  border: 1px solid var(--fg-border);
  background: var(--fg-surface);
  padding: 0.75rem 0.85rem;
  font-weight: 700;
}

.flash-message.success {
  color: var(--fg-success);
}

.flash-message.error {
  color: var(--fg-danger);
}

.state-card {
  border: 1px solid var(--fg-border);
  border-radius: 0.9rem;
  background: var(--fg-surface);
  padding: 1rem;
  color: var(--fg-muted);
}

.verify-list {
  display: grid;
  gap: 1rem;
}

.verify-card {
  border: 1px solid var(--fg-border);
  border-radius: 0.95rem;
  background: var(--fg-surface);
  padding: clamp(0.9rem, 2.2vw, 1.35rem);
  box-shadow: var(--fg-shadow);
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.verify-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.verify-card-top h2 {
  margin: 0;
  font-size: clamp(1.15rem, 1.9vw, 1.35rem);
}

.verify-card-top p {
  margin: 0.3rem 0 0;
  color: var(--fg-muted);
}

.rate-block {
  display: grid;
  justify-items: end;
  gap: 0.2rem;
  text-align: right;
  min-width: 160px;
}

.rate-block span {
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--fg-muted);
  font-size: 0.74rem;
  font-weight: 700;
}

.rate-block strong {
  font-size: 1.65rem;
  letter-spacing: -0.02em;
}

.verify-card-body {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 1rem;
  min-width: 0;
}

.details-column {
  display: grid;
  gap: 0.75rem;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  border: 1px solid var(--fg-border);
  border-radius: 0.85rem;
  overflow: hidden;
}

.metric-item {
  padding: 0.75rem;
  display: grid;
  gap: 0.2rem;
  border-right: 1px solid var(--fg-border);
  border-bottom: 1px solid var(--fg-border);
}

.metric-item:nth-child(2n) {
  border-right: none;
}

.metric-item:nth-last-child(-n + 2) {
  border-bottom: none;
}

.metric-item span {
  color: var(--fg-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.73rem;
  font-weight: 700;
}

.metric-item strong {
  font-size: 1.75rem;
  letter-spacing: -0.03em;
}

.commission-copy {
  margin: 0;
  color: var(--fg-muted);
}

.commission-copy strong {
  color: var(--fg-text);
}

.note-label {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--fg-muted);
  margin-left: 0.25rem;
}

textarea {
  width: 100%;
  border-radius: 0.7rem;
  border: 1px solid var(--fg-border);
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  font-family: inherit;
  font-size: 0.95rem;
  padding: 0.75rem 0.85rem;
  resize: vertical;
  min-height: 88px;
  outline: none;
  transition: all 0.2s ease;
}

textarea:focus {
  border-color: color-mix(in srgb, var(--fg-primary) 40%, var(--fg-border));
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 17%, transparent);
}

.preview-column {
  min-height: 100%;
}

.preview-frame {
  border: 1px solid var(--fg-border);
  border-radius: 0.8rem;
  background: var(--fg-surface-muted);
  min-height: 100%;
  overflow: hidden;
  display: grid;
  min-width: 0;
}

.preview-frame img {
  width: 100%;
  height: 100%;
  max-height: 360px;
  object-fit: cover;
}

.preview-empty {
  min-height: 220px;
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 0.3rem;
  text-align: center;
  color: var(--fg-muted);
  padding: 1rem;
}

.preview-empty .icon {
  font-size: 2.2rem;
}

.preview-empty p {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.preview-empty small {
  font-size: 0.88rem;
}

.verify-card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.action-btn {
  border: 1px solid var(--fg-border);
  background: var(--fg-surface);
  color: var(--fg-text);
  border-radius: 0.65rem;
  padding: 0.6rem 0.85rem;
  font-size: 0.96rem;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: 140ms ease;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.action-btn.neutral {
  background: var(--fg-surface);
}

.action-btn.warning {
  color: #d22f27;
  border-color: color-mix(in srgb, #d22f27 36%, var(--fg-border));
  background: color-mix(in srgb, #d22f27 6%, var(--fg-surface));
}

.action-btn.success {
  color: #f6fff8;
  border-color: #1d8f53;
  background: #1fa861;
}

.action-btn.success:hover:not(:disabled) {
  background: #198850;
}

.icon {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 1.1rem;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  direction: ltr;
  font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}

@media (max-width: 980px) {
  .verify-card-body {
    grid-template-columns: 1fr;
  }

  .preview-frame {
    min-height: 220px;
  }
}

@media (max-width: 780px) {
  .title-row {
    flex-direction: column;
  }

  .refresh-btn {
    width: 100%;
  }

  .stats-strip {
    grid-template-columns: 1fr;
  }

  .rate-block {
    justify-items: start;
    text-align: left;
  }

  .verify-card-top {
    flex-direction: column;
  }

  .verify-card-actions {
    justify-content: stretch;
  }

  .verify-card-actions .action-btn {
    flex: 1;
    justify-content: center;
    min-width: 0;
  }
}
</style>