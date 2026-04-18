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
                :href="toPublicUrl(item.storage_path)"
                target="_blank"
                rel="noopener noreferrer"
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
import { useRuntimeConfig } from '#imports'
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
const config = useRuntimeConfig()

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

const toPublicUrl = (storagePath: string) => {
  // Adjust if your bucket URL strategy differs
  const base = String(config.public?.apiBase || '').replace(/\/$/, '')
  return `${base}/screenshots/file/${encodeURIComponent(storagePath)}`
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
    const qs = new URLSearchParams({ status, note }).toString()
    await authFetch(`/screenshots/${screenshotId}/review?${qs}`, {
      method: 'PATCH'
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
  color: #595c5e;
}

.header-action {
  background: #0545ef;
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
  background: #595c5e;
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

.queue-card {
  background: #ffffff;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 12px 24px -16px rgba(44, 47, 49, 0.18);
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
  color: #0b7a33;
}
.status-message.error {
  color: #d92d20;
}

.queue-state {
  margin-top: 0.9rem;
  color: #595c5e;
  font-size: 0.92rem;
}

.queue-list {
  margin-top: 0.9rem;
  display: grid;
  gap: 0.9rem;
}

.queue-item {
  border: 1px solid #eef1f3;
  border-radius: 0.9rem;
  padding: 0.9rem;
  background: #fbfcfd;
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
  color: #595c5e;
  font-size: 0.84rem;
}
.meta span {
  font-weight: 700;
  color: #2c2f31;
}

.preview-link {
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 700;
  color: #0545ef;
  background: #eef1f3;
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
  color: #595c5e;
}

.review-controls textarea {
  width: 100%;
  border: none;
  border-radius: 0.9rem;
  background: #eef1f3;
  padding: 0.75rem 0.85rem;
  font-family: inherit;
  color: #2c2f31;
  resize: vertical;
  outline: none;
}

.review-controls textarea:focus {
  box-shadow: 0 0 0 2px rgba(5, 69, 239, 0.2);
  background: #ffffff;
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
  background: #e7f8ef;
  color: #0b7a33;
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