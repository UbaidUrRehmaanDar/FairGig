<template>
  <div class="settings-page">
    <main class="settings-main">
      <div class="page-header">
        <div>
          <h1>Settings</h1>
          <p>Manage your profile, preferences, and privacy.</p>
        </div>
        <button type="button" class="header-action" :disabled="isSigningOut" @click="signOut">
          {{ isSigningOut ? 'Signing out...' : 'Logout' }}
        </button>
      </div>

      <section class="panel-card">
        <div class="panel-header">
          <h2>Profile Overview</h2>
          <p class="panel-sub">Basic account info from your session.</p>
        </div>

        <div v-if="user" class="profile-grid">
          <div class="profile-item">
            <div class="label">Email</div>
            <div class="value">{{ user.email || '—' }}</div>
          </div>
          <div class="profile-item">
            <div class="label">User ID</div>
            <div class="value">{{ shortId(user.id) }}</div>
          </div>
          <div class="profile-item">
            <div class="label">Joined</div>
            <div class="value">{{ formatDate(user.created_at) }}</div>
          </div>
        </div>

        <div v-else class="panel-state">Loading session...</div>
      </section>

      <section class="panel-card">
        <div class="panel-header">
          <h2>Identity & Work</h2>
          <p class="panel-sub">Update your working zone and category.</p>
        </div>

        <form class="settings-form" novalidate @submit.prevent="saveProfile">
          <div class="form-grid">
            <div class="input-group">
              <label for="full-name">Full Name</label>
              <div class="input-with-icon">
                <span class="icon">person</span>
                <input id="full-name" v-model.trim="fullName" type="text" placeholder="e.g. Ali Khan" />
              </div>
            </div>

            <div class="input-group">
              <label for="city-zone">Work Zone</label>
              <div class="input-with-icon">
                <span class="icon">location_on</span>
                <select id="city-zone" v-model="cityZone">
                  <option value="">Select zone...</option>
                  <option v-for="z in cityZones" :key="z" :value="z">{{ z }}</option>
                </select>
              </div>
            </div>

            <div class="input-group">
              <label for="category">Platform Category</label>
              <div class="input-with-icon">
                <span class="icon">work</span>
                <select id="category" v-model="platformCategory">
                  <option value="">Select category...</option>
                  <option v-for="c in platformCategories" :key="c.value" :value="c.value">
                    {{ c.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <p v-if="profileMessage" :class="['form-message', profileMessageType]">{{ profileMessage }}</p>

          <div class="actions">
            <button
              type="submit"
              class="primary-button"
              :class="{ 'is-loading': isSavingProfile }"
              :disabled="isSavingProfile"
            >
              <span v-if="!isSavingProfile">Save Profile</span>
              <span v-else>Saving...</span>
            </button>
          </div>
        </form>
      </section>

      <section class="panel-card">
        <div class="panel-header">
          <h2>Preferences</h2>
          <p class="panel-sub">Local preferences saved on this device.</p>
        </div>

        <div class="pref-grid">
          <div class="pref-item">
            <div class="pref-top">
              <div>
                <div class="pref-title">Dark Mode</div>
                <div class="pref-desc">Applies across the whole app.</div>
              </div>

              <label class="switch" for="dark-mode">
                <input id="dark-mode" v-model="darkMode" type="checkbox" @change="applyTheme" />
                <span class="slider" />
              </label>
            </div>
          </div>

          <div class="pref-item">
            <div class="pref-top">
              <div>
                <div class="pref-title">Default Platform</div>
                <div class="pref-desc">Auto-fills in the shift logger.</div>
              </div>
            </div>

            <div class="input-with-icon">
              <span class="icon">directions_car</span>
              <select v-model="defaultPlatform" @change="saveLocalPreferences">
                <option value="">Select platform...</option>
                <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
          </div>

          <div class="pref-item">
            <div class="pref-top">
              <div>
                <div class="pref-title">Demo Persona</div>
                <div class="pref-desc">Just changes the dashboard route (does not change backend permissions).</div>
              </div>
            </div>

            <div class="input-with-icon">
              <span class="icon">switch_account</span>
              <select v-model="demoPersona" @change="switchPersona">
                <option value="worker">Worker</option>
                <option value="verifier">Verifier</option>
                <option value="advocate">Advocate</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      <section class="panel-card">
        <div class="panel-header">
          <h2>Data</h2>
          <p class="panel-sub">Export your data for your own records.</p>
        </div>

        <div class="actions">
          <button type="button" class="ghost-btn" :disabled="isExporting" @click="exportShiftsCsv">
            {{ isExporting ? 'Preparing...' : 'Download Shifts CSV' }}
          </button>
        </div>

        <p v-if="exportMessage" :class="['form-message', exportMessageType]">{{ exportMessage }}</p>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' as any })

import { onMounted, ref } from 'vue'
import { useSupabaseClient } from '#imports'
import { useApi } from '../composables/useApi'
import { useShiftsStore } from '../stores/shifts'

type SessionSnapshot = {
  id: string
  email: string | null
  created_at: string | null
}

const supabase = useSupabaseClient()
const { authFetch } = useApi()
const shiftsStore = useShiftsStore()

const user = ref<SessionSnapshot | null>(null)

const fullName = ref('')
const cityZone = ref('')
const platformCategory = ref('')

const cityZones = ['North', 'Central', 'South', 'East', 'West']
const platformCategories = [
  { label: 'Ride-hailing / Transport', value: 'transport' },
  { label: 'Delivery', value: 'delivery' },
  { label: 'Motorbike / Courier', value: 'courier' },
  { label: 'Other', value: 'other' }
]

const platforms = ['Careem', 'InDrive', 'Bykea', 'Foodpanda', 'Cheetay', 'Other']

const isSavingProfile = ref(false)
const profileMessage = ref('')
const profileMessageType = ref<'success' | 'error'>('success')

const darkMode = ref(false)
const defaultPlatform = ref('')
const demoPersona = ref<'worker' | 'verifier' | 'advocate'>('worker')

const isSigningOut = ref(false)

const isExporting = ref(false)
const exportMessage = ref('')
const exportMessageType = ref<'success' | 'error'>('success')

const shortId = (id: string) => {
  if (!id) return ''
  return id.length > 10 ? `${id.slice(0, 6)}…${id.slice(-4)}` : id
}

const formatDate = (iso: string | null | undefined) => {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' })
}

const applyTheme = () => {
  try {
    const next = darkMode.value ? 'dark' : 'light'
    window.localStorage.setItem('fg_theme', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
  } catch {
    document.documentElement.classList.toggle('dark', darkMode.value)
  }
}

const saveLocalPreferences = () => {
  try {
    window.localStorage.setItem('fg_default_platform', defaultPlatform.value || '')
    window.localStorage.setItem('fg_demo_persona', demoPersona.value)
  } catch {
    // ignore
  }
}

const switchPersona = async () => {
  saveLocalPreferences()
  await navigateTo(`/dashboard/${demoPersona.value}`)
}

const saveProfile = async () => {
  if (isSavingProfile.value) return
  profileMessage.value = ''

  if (!fullName.value || !cityZone.value || !platformCategory.value) {
    profileMessageType.value = 'error'
    profileMessage.value = 'Please fill full name, work zone, and category.'
    return
  }

  isSavingProfile.value = true
  try {
    await authFetch('/auth/setup-profile', {
      method: 'POST',
      body: JSON.stringify({
        full_name: fullName.value,
        city_zone: cityZone.value,
        platform_category: platformCategory.value,
        role: 'worker'
      })
    })

    profileMessageType.value = 'success'
    profileMessage.value = 'Profile saved.'
  } catch (e: any) {
    profileMessageType.value = 'error'
    profileMessage.value = e?.message || 'Failed to save profile.'
  } finally {
    isSavingProfile.value = false
  }
}

const shiftsToCsv = (rows: any[]) => {
  const headers = [
    'shift_date',
    'platform',
    'hours_worked',
    'gross_earned',
    'platform_deductions',
    'net_received',
    'verification_status'
  ]

  const escape = (value: any) => {
    const s = value === null || value === undefined ? '' : String(value)
    if (/[\n\r,\"]/g.test(s)) return `"${s.replace(/\"/g, '""')}"`
    return s
  }

  const lines = [headers.join(',')]
  for (const r of rows) {
    lines.push(headers.map((h) => escape((r as any)[h])).join(','))
  }

  return lines.join('\n')
}

const exportShiftsCsv = async () => {
  if (isExporting.value) return
  exportMessage.value = ''

  isExporting.value = true
  try {
    await shiftsStore.fetchShifts()
    const csv = shiftsToCsv(shiftsStore.shifts || [])

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = `fairgig-shifts-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()

    URL.revokeObjectURL(url)

    exportMessageType.value = 'success'
    exportMessage.value = 'CSV downloaded.'
  } catch (e: any) {
    exportMessageType.value = 'error'
    exportMessage.value = e?.message || 'Failed to export shifts.'
  } finally {
    isExporting.value = false
  }
}

const signOut = async () => {
  if (isSigningOut.value) return
  isSigningOut.value = true
  try {
    await supabase.auth.signOut()
    await navigateTo('/login')
  } finally {
    isSigningOut.value = false
  }
}

onMounted(async () => {
  const { data } = await supabase.auth.getSession()
  const currentUser = data.session?.user || null
  user.value = currentUser
    ? {
        id: String(currentUser.id || ''),
        email: typeof currentUser.email === 'string' ? currentUser.email : null,
        created_at: typeof currentUser.created_at === 'string' ? currentUser.created_at : null,
      }
    : null

  try {
    const t = window.localStorage.getItem('fg_theme')
    darkMode.value = t === 'dark'
  } catch {
    darkMode.value = document.documentElement.classList.contains('dark')
  }

  try {
    defaultPlatform.value = window.localStorage.getItem('fg_default_platform') || ''
    const savedPersona = (window.localStorage.getItem('fg_demo_persona') as any) || 'worker'
    if (['worker', 'verifier', 'advocate'].includes(savedPersona)) demoPersona.value = savedPersona
  } catch {
    // ignore
  }

  applyTheme()
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
}

.settings-main {
  max-width: 1120px;
  margin: 0 auto;
  padding: 1.4rem 1rem 2.6rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.2rem;
}
.page-header h1 {
  margin: 0;
  font-size: 2rem;
  letter-spacing: -0.02em;
}
.page-header p {
  margin: 0.25rem 0 0;
  color: var(--fg-muted);
  font-weight: 600;
}

/* Top action - same UX language */
.header-action {
  width: 11rem;
  height: 3rem;
  border: 1px solid transparent;
  background: var(--fg-primary);
  color: #fff;
  font-weight: 900;
  border-radius: 9999px;
  cursor: pointer;
  box-shadow: var(--fg-shadow);
  transition:
    border-radius 0ms linear,
    background-color 120ms linear,
    color 120ms linear,
    border-color 120ms linear,
    box-shadow 140ms ease;
}
.header-action:hover:not(:disabled) {
  border-radius: 1rem;
  background: var(--fg-surface);
  color: var(--fg-primary);
  border-color: var(--fg-border);
  box-shadow: var(--fg-shadow);
}
.header-action:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 25%, transparent);
}
.header-action:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.panel-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1.2rem;
  padding: 1.1rem;
  margin-bottom: 1rem;
  box-shadow: var(--fg-shadow);
  transition:
    transform 170ms cubic-bezier(0.2, 0.8, 0.2, 1),
    box-shadow 170ms ease,
    border-color 140ms ease;
}
.panel-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--fg-primary) 30%, var(--fg-border));
  box-shadow: 0 16px 28px -18px color-mix(in srgb, var(--fg-primary) 45%, transparent);
}

.panel-header {
  margin-bottom: 0.85rem;
}
.panel-header h2 {
  margin: 0;
  font-size: 1.1rem;
}
.panel-sub {
  margin: 0.2rem 0 0;
  color: var(--fg-muted);
  font-weight: 600;
  font-size: 0.92rem;
}

.panel-state {
  color: var(--fg-muted);
  font-weight: 700;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}
.profile-item {
  border: 1px solid var(--fg-border);
  background: var(--fg-surface-muted);
  border-radius: 1rem;
  padding: 0.85rem;
}
.profile-item .label {
  color: var(--fg-muted);
  font-weight: 800;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.profile-item .value {
  margin-top: 0.35rem;
  font-weight: 800;
}

.settings-form .form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}

.input-group label {
  display: block;
  font-weight: 800;
  margin-bottom: 0.35rem;
}

.input-with-icon {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  border: 1px solid var(--fg-border);
  background: var(--fg-surface);
  border-radius: 0.95rem;
  padding: 0.65rem 0.75rem;
  transition: border-color 120ms ease, box-shadow 120ms ease;
}
.input-with-icon:focus-within {
  border-color: color-mix(in srgb, var(--fg-primary) 45%, var(--fg-border));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 15%, transparent);
}

.input-with-icon .icon {
  font-family: 'Material Symbols Outlined';
  font-size: 1.15rem;
  color: var(--fg-muted);
}

.input-with-icon input,
.input-with-icon select {
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--fg-text);
  font-size: 16px;
}

.actions {
  margin-top: 0.9rem;
  display: flex;
  gap: 0.65rem;
}

/* Primary button style matching your language */
.primary-button {
  width: 12rem;
  height: 3rem;
  border: 1px solid transparent;
  background: var(--fg-primary);
  color: #fff;
  font-weight: 900;
  border-radius: 9999px;
  cursor: pointer;
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
.primary-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.primary-button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 25%, transparent);
}

/* Ghost button with inversion hover */
.ghost-btn {
  border: 1px solid var(--fg-border);
  background: var(--fg-surface);
  color: var(--fg-text);
  font-weight: 900;
  width: 14rem;
  height: 3rem;
  border-radius: 9999px;
  cursor: pointer;
  box-shadow: var(--fg-shadow);
  transition:
    border-radius 0ms linear,
    background-color 120ms linear,
    color 120ms linear,
    border-color 120ms linear,
    box-shadow 140ms ease;
}
.ghost-btn:hover:not(:disabled) {
  border-radius: 1rem;
  background: var(--fg-primary);
  color: #fff;
  border-color: transparent;
  box-shadow: var(--fg-shadow);
}
.ghost-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}
.ghost-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.form-message {
  margin: 0.75rem 0 0;
  font-weight: 800;
}
.form-message.success {
  color: var(--fg-success);
}
.form-message.error {
  color: var(--fg-danger);
}

.pref-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}

.pref-item {
  border: 1px solid var(--fg-border);
  background: var(--fg-surface-muted);
  border-radius: 1rem;
  padding: 0.9rem;
  transition:
    transform 170ms cubic-bezier(0.2, 0.8, 0.2, 1),
    box-shadow 170ms ease,
    border-color 140ms ease;
}
.pref-item:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--fg-primary) 30%, var(--fg-border));
  box-shadow: 0 14px 24px -18px color-mix(in srgb, var(--fg-primary) 45%, transparent);
}

.pref-top {
  display: flex;
  justify-content: space-between;
  gap: 0.85rem;
  align-items: center;
  margin-bottom: 0.65rem;
}

.pref-title {
  font-weight: 900;
}

.pref-desc {
  margin-top: 0.15rem;
  color: var(--fg-muted);
  font-weight: 600;
  font-size: 0.9rem;
}

/* Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background-color: var(--fg-border);
  transition: 0.2s;
  border-radius: 9999px;
}
.slider:before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: var(--fg-surface);
  transition: 0.2s;
  border-radius: 50%;
}
input:checked + .slider {
  background-color: color-mix(in srgb, var(--fg-primary) 70%, var(--fg-border));
}
input:checked + .slider:before {
  transform: translateX(20px);
}

@media (max-width: 900px) {
  .profile-grid,
  .settings-form .form-grid,
  .pref-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .settings-main {
    padding: 1rem 0.85rem 5.5rem;
  }
  .page-header {
    flex-direction: column;
    gap: 0.85rem;
  }
  .header-action {
    width: 100%;
    text-align: center;
  }
  .actions {
    flex-direction: column;
  }
  .actions button {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .panel-card,
  .pref-item,
  .header-action,
  .primary-button,
  .ghost-btn {
    transition: none !important;
  }
}
</style>