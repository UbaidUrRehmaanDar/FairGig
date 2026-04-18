<template>
  <div class="verifier-dashboard-page">
    <main class="dashboard-main">
      <div class="page-header">
        <div>
          <h1>Verifier Dashboard</h1>
          <p>Review uploaded earnings screenshots and update verification status.</p>
        </div>
        <button
          type="button"
          class="header-action"
          :disabled="isLoading"
          @click="loadPending"
        >
          {{ isLoading ? 'Refreshing...' : 'Refresh Queue' }}
        </button>
      </div>

      <section class="summary-grid">
        <article class="summary-card">
          <div class="card-label">Pending</div>
          <div class="card-value">{{ pendingCount }}</div>
        </article>
        <article class="summary-card">
          <div class="card-label">Reviewed (Session)</div>
          <div class="card-value">{{ reviewedCount }}</div>
        </article>
        <article class="summary-card">
          <div class="card-label">Approved (Session)</div>
          <div class="card-value highlight">{{ approvedCount }}</div>
        </article>
      </section>

      <section class="queue-card">
        <div class="queue-header">
          <h2>Pending Verification Queue</h2>
          <p v-if="message" :class="['status-message', messageType]">{{ message }}</p>
        </div>

        <div v-if="isLoading" class="queue-state">Loading pending screenshots...</div>
        <div v-else-if="!queue.length" class="queue-state">
          No pending screenshots right now. You’re all caught up.
        </div>

        <div v-else class="queue-list">
          <article class="queue-item" v-for="item in queue" :key="item.id">
            <div class="item-top">
              <div class="meta">
                <h3>Screenshot #{{ shortId(item.id) }}</h3>
                <p>
                  Shift ID:
                  <span>{{ shortId(item.shift_id) }}</span>
                </p>
                <p>
                  Worker ID:
                  <span>{{ shortId(item.worker_id) }}</span>
                </p>
              </div>

              <a
                class="preview-link"
                href="#"
                @click.prevent="openScreenshot(item.id)"
              >
                Open Image
              </a>
            </div>

            <div class="review-controls">
              <label :for="`note-${item.id}`">Verifier Note (optional)</label>
              <textarea
                :id="`note-${item.id}`"
                v-model.trim="notes[item.id]"
                rows="2"
                placeholder="Add context for worker/advocate..."
              />

              <div class="action-row">
                <button
                  type="button"
                  class="action-btn approve"
                  :disabled="isBusy[item.id]"
                  @click="review(item.id, 'verified')"
                >
                  {{ isBusy[item.id] ? 'Saving...' : 'Approve' }}
                </button>

                <button
                  type="button"
                  class="action-btn flag"
                  :disabled="isBusy[item.id]"
                  @click="review(item.id, 'flagged')"
                >
                  {{ isBusy[item.id] ? 'Saving...' : 'Flag' }}
                </button>

                <button
                  type="button"
                  class="action-btn unverifiable"
                  :disabled="isBusy[item.id]"
                  @click="review(item.id, 'unverifiable')"
                >
                  {{ isBusy[item.id] ? 'Saving...' : 'Mark Unverifiable' }}
                </button>
              </div>
            </div>
          </article>
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

import { computed, reactive, ref } from 'vue'
import { useApi } from '../../composables/useApi'

type PendingItem = {
  id: string
  shift_id: string
  worker_id: string
  storage_path: string
  status: string
  created_at: string
}

const { authFetch } = useApi()

const queue = ref<PendingItem[]>([])
const isLoading = ref(false)
const reviewedCount = ref(0)
const approvedCount = ref(0)

const notes = reactive<Record<string, string>>({})
const isBusy = reactive<Record<string, boolean>>({})

const message = ref('')
const messageType = ref<'error' | 'success'>('success')

const pendingCount = computed(() => queue.value.length)

const shortId = (v?: string) => {
  const s = String(v || '')
  if (s.length <= 8) return s || '—'
  return `${s.slice(0, 8)}...`
}

const openScreenshot = async (screenshotId: string) => {
  message.value = ''
  try {
    const data = await authFetch<{ signed_url?: string }>(
      `/screenshots/view/${encodeURIComponent(screenshotId)}?redirect=false`
    )
    const signedUrl = String(data?.signed_url || '').trim()
    if (!signedUrl) {
      throw new Error('Screenshot URL is unavailable.')
    }

    if (typeof window !== 'undefined') {
      window.open(signedUrl, '_blank', 'noopener,noreferrer')
    }
  } catch (e: any) {
    messageType.value = 'error'
    message.value = e?.message || 'Failed to open screenshot.'
  }
}

const loadPending = async () => {
  isLoading.value = true
  message.value = ''
  try {
    const data = await authFetch('/screenshots/pending')
    queue.value = Array.isArray(data) ? data : []
  } catch (e: any) {
    messageType.value = 'error'
    message.value = e?.message || 'Failed to load pending queue.'
  } finally {
    isLoading.value = false
  }
}

const review = async (screenshotId: string, status: 'verified' | 'flagged' | 'unverifiable') => {
  isBusy[screenshotId] = true
  message.value = ''

  try {
    const note = notes[screenshotId] || ''
    await authFetch(`/screenshots/${screenshotId}/review`, {
      method: 'PATCH',
      body: {
        status,
        note
      }
    })

    reviewedCount.value += 1
    if (status === 'verified') approvedCount.value += 1

    queue.value = queue.value.filter((item) => item.id !== screenshotId)
    delete notes[screenshotId]

    messageType.value = 'success'
    message.value = 'Review saved successfully.'
  } catch (e: any) {
    messageType.value = 'error'
    message.value = e?.message || 'Failed to save review.'
  } finally {
    isBusy[screenshotId] = false
  }
}

await loadPending()
</script>

<style scoped>
.verifier-dashboard-page {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
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
  justify-content: space-between;
  align-items: flex-start;
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

.header-action {
  background: var(--fg-primary);
  color: #f2f1ff;
  border: none;
  border-radius: 9999px;
  padding: 0.7rem 1rem;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
}
.header-action:disabled {
  cursor: not-allowed;
  background: var(--fg-muted);
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

.queue-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--fg-shadow);
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.queue-header h2 {
  font-size: 1.1rem;
  font-weight: 800;
}

.status-message {
  font-size: 0.82rem;
  font-weight: 700;
}
.status-message.success {
  color: var(--fg-success);
}
.status-message.error {
  color: var(--fg-danger);
}

.queue-state {
  margin-top: 0.9rem;
  color: var(--fg-muted);
  font-size: 0.92rem;
}

.queue-list {
  margin-top: 0.9rem;
  display: grid;
  gap: 0.9rem;
}

.queue-item {
  border: 1px solid var(--fg-border);
  border-radius: 0.9rem;
  padding: 0.9rem;
  background: var(--fg-surface-muted);
}

.item-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.8rem;
}

.meta h3 {
  font-size: 1rem;
  font-weight: 800;
}

.meta p {
  margin-top: 0.25rem;
  color: var(--fg-muted);
  font-size: 0.84rem;
}
.meta span {
  font-weight: 700;
  color: var(--fg-text);
}

.preview-link {
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--fg-primary);
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 9999px;
  padding: 0.45rem 0.7rem;
  white-space: nowrap;
}

.review-controls {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.55rem;
}

.review-controls label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--fg-muted);
}

.review-controls textarea {
  width: 100%;
  border: none;
  border-radius: 0.9rem;
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  padding: 0.75rem 0.85rem;
  font-family: inherit;
  color: var(--fg-text);
  resize: vertical;
  outline: none;
}

.review-controls textarea:focus {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 20%, transparent);
  background: var(--fg-surface);
}

.action-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  border: none;
  border-radius: 9999px;
  padding: 0.5rem 0.85rem;
  font-weight: 700;
  font-size: 0.78rem;
  cursor: pointer;
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.action-btn.approve {
  background: color-mix(in srgb, var(--fg-success) 14%, var(--fg-surface));
  color: var(--fg-success);
}
.action-btn.flag {
  background: #fff6df;
  color: #8a5b00;
}
.action-btn.unverifiable {
  background: #ffe9e9;
  color: #8a1f1f;
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
}

@media (min-width: 700px) {
  .summary-grid {
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