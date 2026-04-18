<template>
  <div class="confirm-container">
    <section class="left-section">
      <div class="content">
        <div class="logo">FairGig</div>
        <div class="main-text">
          <h1>Account confirmation in progress.</h1>
          <p>
            We’re securely validating your email confirmation and preparing your account for access.
          </p>
        </div>
      </div>
    </section>

    <main class="right-section">
      <div class="form-container">
        <div class="mobile-logo">FairGig</div>

        <div class="form-header">
          <h2>Confirming your account</h2>
          <p>{{ statusMessage }}</p>
        </div>

        <div class="status-box" :class="statusClass">
          <span class="icon status-icon">{{ statusIcon }}</span>
          <span>{{ statusLabel }}</span>
        </div>

        <div class="actions">
          <button
            type="button"
            class="primary-button"
            :class="{ 'is-loading': isBusy }"
            :disabled="isBusy"
            @click="goNext"
          >
            <span v-if="isBusy">Processing...</span>
            <span v-else>{{ nextButtonText }}</span>
          </button>
        </div>

        <div class="alt-links">
          <p>
            Need help?
            <NuxtLink to="/login">Return to login</NuxtLink>
          </p>
        </div>
      </div>
    </main>

    <div class="support-fab">
      <button>
        <span class="icon">help_outline</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { navigateTo } from 'nuxt/app'
import { useRoute } from 'vue-router'
import { useSupabaseClient } from '#imports'

import { useApi } from '../composables/useApi'

const supabase = useSupabaseClient()
const { authFetch } = useApi()
const isBusy = ref(true)
const status = ref<'pending' | 'success' | 'error'>('pending')
const statusMessage = ref('Please wait while we verify your confirmation link.')
const redirectPath = ref('/login')

const roleToPath = (role: string) => {
  if (role === 'advocate') return '/dashboard/advocate'
  if (role === 'verifier') return '/dashboard/verifier'
  return '/dashboard/worker'
}

const resolveRole = (user: any) => {
  const candidate =
    (typeof user?.user_metadata?.role === 'string' && user.user_metadata.role) ||
    (typeof user?.app_metadata?.role === 'string' && user.app_metadata.role) ||
    'worker'

  const normalized = String(candidate).toLowerCase().trim()
  if (normalized === 'advocate') return 'advocate'
  if (normalized === 'verifier') return 'verifier'
  return 'worker'
}

const fallbackNameFromEmail = (emailValue: string) => {
  const localPart = String(emailValue || '').split('@')[0] || 'Worker'
  return localPart
    .replace(/[._-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

const ensureProfile = async (user: any, role: string) => {
  const fullName =
    String(user?.user_metadata?.full_name || '').trim() ||
    fallbackNameFromEmail(String(user?.email || '').trim())

  try {
    await authFetch('/auth/setup-profile', {
      method: 'POST',
      body: JSON.stringify({
        full_name: fullName,
        city_zone: String(user?.user_metadata?.city_zone || 'Unknown'),
        platform_category: String(user?.user_metadata?.platform_category || 'ride_hailing'),
        role
      })
    })
  } catch {
    // Keep confirmation flow non-blocking if profile setup temporarily fails.
  }
}

const waitForSessionUser = async () => {
  for (let attempt = 0; attempt < 6; attempt += 1) {
    const { data } = await supabase.auth.getSession()
    if (data.session?.user) {
      return data.session.user
    }
    if (attempt < 5) {
      await new Promise((resolve) => setTimeout(resolve, 250))
    }
  }
  return null
}

const statusLabel = computed(() => {
  if (status.value === 'success') return 'Email confirmed successfully'
  if (status.value === 'error') return 'Confirmation failed'
  return 'Validating link'
})

const statusClass = computed(() => {
  if (status.value === 'success') return 'ok'
  if (status.value === 'error') return 'bad'
  return 'pending'
})

const statusIcon = computed(() => {
  if (status.value === 'success') return 'check_circle'
  if (status.value === 'error') return 'error'
  return 'schedule'
})

const nextButtonText = computed(() => {
  if (status.value === 'success') return 'Continue to Dashboard'
  if (status.value === 'error') return 'Go to Login'
  return 'Please wait...'
})

onMounted(async () => {
  try {
    const route = useRoute()
    const hasTokenLikeParams =
      Boolean(route.query.token) ||
      Boolean(route.query.access_token) ||
      Boolean(route.query.refresh_token) ||
      Boolean(route.hash)

    await new Promise((resolve) => setTimeout(resolve, 900))

    const user = await waitForSessionUser()
    if (user) {
      const role = resolveRole(user)
      await ensureProfile(user, role)
      redirectPath.value = roleToPath(role)
      status.value = 'success'
      statusMessage.value = 'Your account is confirmed. You can continue now.'
    } else if (hasTokenLikeParams) {
      status.value = 'error'
      statusMessage.value = 'Could not establish a confirmed session from this link. Please try logging in again.'
      redirectPath.value = '/login'
    } else {
      status.value = 'error'
      statusMessage.value = 'Confirmation link is invalid or expired. Please log in again.'
      redirectPath.value = '/login'
    }
  } catch {
    status.value = 'error'
    statusMessage.value = 'Something went wrong during confirmation.'
    redirectPath.value = '/login'
  } finally {
    isBusy.value = false
  }
})

const goNext = async () => {
  if (isBusy.value) return
  await navigateTo(redirectPath.value)
}
</script>

<style scoped>
.confirm-container {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
  background-color: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
}

.left-section {
  display: none;
  width: 50%;
  position: relative;
  flex-direction: column;
  justify-content: space-between;
  padding: 3rem;
  color: #f2f1ff;
  overflow: hidden;
  background:
    linear-gradient(rgba(5, 69, 239, 0.62), rgba(5, 69, 239, 0.62)),
    url('https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1600&q=80')
      center / cover no-repeat;
}

.left-section::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(1200px 500px at -10% -20%, rgba(255, 255, 255, 0.22), transparent 55%),
    radial-gradient(900px 500px at 120% 120%, rgba(0, 0, 0, 0.25), transparent 60%);
  mix-blend-mode: soft-light;
}

.left-section .content {
  position: relative;
  z-index: 10;
}
.left-section .logo {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.05em;
}
.left-section .main-text {
  margin-top: 10rem;
}
.left-section h1 {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.1;
  max-width: 36rem;
}
.left-section p {
  margin-top: 2rem;
  font-size: 1.125rem;
  max-width: 32rem;
  line-height: 1.75;
  opacity: 0.86;
}

.right-section {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}
.form-container {
  width: 100%;
  max-width: 28rem;
}
.mobile-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: var(--fg-primary);
}
.form-header {
  text-align: center;
  margin-bottom: 2rem;
}
.form-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}
.form-header p {
  margin-top: 0.5rem;
  color: var(--fg-muted);
}

.status-box {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  border-radius: 1rem;
  padding: 0.95rem 1rem;
  font-weight: 600;
  background: var(--fg-surface);
  color: var(--fg-muted);
  border: 1px solid var(--fg-border);
}
.status-box.pending {
  background: var(--fg-surface);
  color: var(--fg-muted);
}
.status-box.ok {
  background: color-mix(in srgb, var(--fg-success) 14%, var(--fg-surface));
  color: var(--fg-success);
}
.status-box.bad {
  background: color-mix(in srgb, var(--fg-danger) 14%, var(--fg-surface));
  color: var(--fg-danger);
}
.status-icon {
  font-size: 1.2rem;
}

.actions {
  padding-top: 1.25rem;
  display: flex;
  justify-content: center;
}
.primary-button {
  width: 18rem;
  height: 3.2rem;
  background-color: var(--fg-primary);
  color: #f2f1ff;
  border: none;
  border-radius: 9999px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 120ms linear, box-shadow 140ms ease;
  box-shadow: var(--fg-shadow);
}
.primary-button:hover:not(:disabled) {
  filter: brightness(0.95);
}
.primary-button.is-loading,
.primary-button:disabled {
  cursor: not-allowed;
  background-color: var(--fg-muted);
  box-shadow: var(--fg-shadow);
}

.alt-links {
  margin-top: 2rem;
  text-align: center;
}
.alt-links p {
  color: var(--fg-muted);
  font-size: 0.875rem;
}
.alt-links a {
  color: var(--fg-primary);
  font-weight: 700;
  text-decoration: none;
  margin-left: 0.25rem;
}
.alt-links a:hover {
  text-decoration: underline;
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

@media (min-width: 1024px) {
  .left-section {
    display: flex;
  }
  .right-section {
    width: 50%;
  }
  .mobile-logo {
    display: none;
  }
  .form-header {
    text-align: left;
  }
}

.icon {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  line-height: 1;
  letter-spacing: normal;
  display: inline-block;
  white-space: nowrap;
  direction: ltr;
  font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}
</style>