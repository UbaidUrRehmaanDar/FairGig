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
  background: var(--fg-primary);
  color: #fff;
  border: none;
  border-radius: 9999px;
  padding: 0.75rem 1.25rem;
  font-weight: 800;
  font-size: 0.9rem;
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
  cursor: not-allowed;
  background: var(--fg-muted);
  opacity: 0.7;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 1rem;
}

.summary-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1.25rem;
  padding: 1.25rem;
  box-shadow: var(--fg-shadow);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.card-label {
  color: var(--fg-muted);
  font-size: 0.86rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.card-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--fg-text);
}

.card-value.highlight {
  color: var(--fg-primary);
}

.queue-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1.25rem;
  padding: 1.25rem;
  box-shadow: var(--fg-shadow);
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.queue-header h2 {
  font-size: 1.15rem;
  font-weight: 800;
}

.status-message {
  font-size: 0.88rem;
  font-weight: 700;
}
.status-message.success {
  color: var(--fg-success);
}
.status-message.error {
  color: var(--fg-danger);
}

.queue-state {
  margin-top: 1rem;
  color: var(--fg-muted);
  font-size: 0.95rem;
  font-weight: 600;
  text-align: center;
  padding: 2rem 0;
}

.queue-list {
  margin-top: 1rem;
  display: grid;
  gap: 1rem;
}

.queue-item {
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  background: var(--fg-surface-muted);
  transition: transform 0.2s ease;
}

.item-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.meta h3 {
  font-size: 1.05rem;
  font-weight: 800;
}

.meta p {
  margin-top: 0.35rem;
  color: var(--fg-muted);
  font-size: 0.88rem;
  font-weight: 600;
}
.meta span {
  font-weight: 800;
  color: var(--fg-text);
}

.preview-link {
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--fg-primary);
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 9999px;
  padding: 0.5rem 1rem;
  white-space: nowrap;
  transition: all 0.2s ease;
}
.preview-link:hover {
  background: var(--fg-primary);
  color: #fff;
  border-color: var(--fg-primary);
}

.review-controls {
  margin-top: 1rem;
  display: grid;
  gap: 0.75rem;
}

.review-controls label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--fg-muted);
  margin-left: 0.25rem;
}

.review-controls textarea {
  width: 100%;
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  background: var(--fg-surface);
  padding: 0.85rem 1rem;
  font-family: inherit;
  color: var(--fg-text);
  resize: vertical;
  outline: none;
  transition: all 0.2s ease;
}

.review-controls textarea:focus {
  border-color: var(--fg-primary);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--fg-primary) 10%, transparent);
}

.action-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.action-btn {
  height: 2.75rem;
  border: none;
  border-radius: 9999px;
  padding: 0 1.25rem;
  font-weight: 800;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.action-btn.approve {
  background: color-mix(in srgb, var(--fg-success) 10%, transparent);
  color: var(--fg-success);
}
.action-btn.approve:hover:not(:disabled) {
  background: var(--fg-success);
  color: #fff;
}

.action-btn.flag {
  background: #fff6df;
  color: #8a5b00;
}
.action-btn.flag:hover:not(:disabled) {
  background: #8a5b00;
  color: #fff;
}

.action-btn.unverifiable {
  background: #ffe9e9;
  color: #8a1f1f;
}
.action-btn.unverifiable:hover:not(:disabled) {
  background: #8a1f1f;
  color: #fff;
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
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fg-primary);
  border: 1px solid var(--fg-border);
  cursor: pointer;
  transition: all 0.2s ease;
}
.support-fab button:hover {
  transform: scale(1.05);
}

@media (min-width: 700px) {
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
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
  .item-top {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }
  .preview-link {
    text-align: center;
  }
  .action-btn {
    flex: 1;
    min-width: 120px;
  }
}
</style>