<template>
  <div class="grievance-board-page">
    <main class="board-main">
      <div class="page-header">
        <div>
          <h1>Worker Grievance Board</h1>
          <p>Community-reported issues across platforms, with advocate escalation support.</p>
        </div>
        <NuxtLink to="/grievances/new" class="header-action">+ Post Grievance</NuxtLink>
      </div>

      <section class="filters-card">
        <div class="filters-grid">
          <div class="input-group">
            <label for="platform-filter">Platform</label>
            <div class="input-with-icon">
              <span class="icon">business</span>
              <select id="platform-filter" v-model="filterPlatform" @change="load">
                <option value="">All Platforms</option>
                <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
          </div>

          <div class="input-group">
            <label for="category-filter">Category</label>
            <div class="input-with-icon">
              <span class="icon">category</span>
              <select id="category-filter" v-model="filterCategory" @change="load">
                <option value="">All Categories</option>
                <option value="commission_change">Commission Change</option>
                <option value="deactivation">Deactivation</option>
                <option value="payment_delay">Payment Delay</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div class="input-group">
            <label for="status-filter">Status</label>
            <div class="input-with-icon">
              <span class="icon">rule</span>
              <select id="status-filter" v-model="filterStatus" @change="load">
                <option value="">All Statuses</option>
                <option value="open">Open</option>
                <option value="escalated">Escalated</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      <section class="list-card">
        <div class="list-header">
          <h2>Recent Grievances</h2>
          <span class="count-pill">{{ grievances.length }} items</span>
        </div>

        <div v-if="loading" class="list-state">Loading grievances...</div>
        <div v-else-if="!grievances.length" class="list-state">
          No grievances found for selected filters.
        </div>

        <div v-else class="grievance-list">
          <article class="grievance-item" v-for="g in grievances" :key="g.id">
            <div class="item-top">
              <div class="tags">
                <span class="platform-pill">{{ g.platform }}</span>
                <span :class="['status-pill', normalizeStatus(g.status)]">{{ g.status }}</span>
                <span class="category-pill">{{ g.category }}</span>
              </div>
              <span class="date">{{ formatDate(g.created_at) }}</span>
            </div>

            <h3>{{ g.title }}</h3>
            <p class="description">{{ g.description }}</p>

            <div class="item-bottom">
              <button class="vote-btn" type="button" @click="upvote(g.id)">👍 {{ g.upvotes || 0 }}</button>

              <button
                v-if="canEscalate && String(g.status).toLowerCase() === 'open'"
                class="escalate-btn"
                type="button"
                @click="escalate(g.id)"
              >
                Escalate
              </button>
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

import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useApi } from '../../composables/useApi'
import { useAuthStore } from '../../stores/auth'

const { authFetch } = useApi()
const authStore = useAuthStore()
const { role } = storeToRefs(authStore)

const grievances = ref<any[]>([])
const loading = ref(false)

const filterPlatform = ref('')
const filterCategory = ref('')
const filterStatus = ref('')

const platforms = ['Careem', 'InDrive', 'Bykea', 'Foodpanda', 'Cheetay', 'Other']

const canEscalate = computed(() => String(role.value || '').toLowerCase() === 'advocate')

const normalizeStatus = (status: string) => String(status || 'open').toLowerCase()

const formatDate = (d: string) => {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-PK')
}

const load = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filterPlatform.value) params.set('platform', filterPlatform.value)
    if (filterCategory.value) params.set('category', filterCategory.value)
    if (filterStatus.value) params.set('status', filterStatus.value)

    const qs = params.toString()
    grievances.value = await authFetch(`/grievances${qs ? `?${qs}` : ''}`)
  } finally {
    loading.value = false
  }
}

const upvote = async (id: string) => {
  await authFetch(`/grievances/${id}/upvote`, { method: 'POST' })
  await load()
}

const escalate = async (id: string) => {
  await authFetch(`/grievances/${id}/escalate`, { method: 'PATCH' })
  await load()
}

await load()
</script>

<style scoped>
.grievance-board-page {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
  padding: 2rem;
}
.board-main {
  max-width: 1080px;
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
.list-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--fg-shadow);
}
.filters-grid {
  display: grid;
  gap: 0.8rem;
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
.input-with-icon select:focus {
  background: var(--fg-surface);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.list-header h2 {
  font-size: 1.06rem;
  font-weight: 800;
}
.count-pill {
  background: var(--fg-surface-muted);
  border-radius: 9999px;
  padding: 0.3rem 0.65rem;
  font-size: 0.76rem;
  font-weight: 700;
}
.list-state {
  margin-top: 0.75rem;
  color: var(--fg-muted);
}

.grievance-list {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.75rem;
}
.grievance-item {
  border: 1px solid var(--fg-border);
  border-radius: 0.95rem;
  padding: 0.85rem;
  background: var(--fg-surface-muted);
}
.item-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.7rem;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.platform-pill,
.status-pill,
.category-pill {
  border-radius: 9999px;
  padding: 0.2rem 0.55rem;
  font-size: 0.72rem;
  font-weight: 700;
}
.platform-pill {
  background: color-mix(in srgb, var(--fg-primary) 14%, var(--fg-surface));
  color: var(--fg-primary);
}
.category-pill {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  color: var(--fg-muted);
}
.status-pill.open {
  background: #fff6df;
  color: #8a5b00;
}
.status-pill.escalated {
  background: #ffe9e9;
  color: #8a1f1f;
}
.status-pill.resolved {
  background: color-mix(in srgb, var(--fg-success) 14%, var(--fg-surface));
  color: var(--fg-success);
}
.date {
  color: var(--fg-muted);
  font-size: 0.8rem;
}

.grievance-item h3 {
  margin-top: 0.65rem;
  font-size: 1rem;
  font-weight: 800;
}
.description {
  margin-top: 0.4rem;
  color: var(--fg-muted);
  font-size: 0.9rem;
  line-height: 1.45;
}

.item-bottom {
  margin-top: 0.75rem;
  display: flex;
  gap: 0.5rem;
}
.vote-btn,
.escalate-btn {
  border: none;
  border-radius: 9999px;
  padding: 0.45rem 0.75rem;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}
.vote-btn {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  color: var(--fg-text);
}
.escalate-btn {
  background: var(--fg-primary);
  color: #f2f1ff;
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

@media (min-width: 860px) {
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