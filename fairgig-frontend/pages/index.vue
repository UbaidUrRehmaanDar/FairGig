<template>
  <div class="auth-index">
    <!-- Left Brand Panel -->
    <section class="left-panel">
      <div class="left-content">
        <div class="logo">FairGig</div>
        <div class="hero-copy">
          <h1>Welcome back to FairGig.</h1>
          <p>
            Empowering the future of independent work with fair pay, better benefits, and total
            transparency.
          </p>
        </div>
      </div>
    </section>

    <!-- Right Session Panel -->
    <main class="right-panel">
      <div class="form-shell">
        <div class="mobile-logo">FairGig</div>

        <div class="header">
          <h2>{{ title }}</h2>
          <p>{{ subtitle }}</p>
        </div>

        <div class="status-chip" aria-live="polite">
          <span class="icon" :class="{ spin: state === 'checking' }">{{ statusIcon }}</span>
          <span>{{ statusText }}</span>
        </div>

        <div class="actions">
          <button
            type="button"
            class="primary-button"
            :class="{ 'is-loading': state === 'checking' }"
            :disabled="state === 'checking'"
            @click="primaryAction"
          >
            <span>{{ primaryLabel }}</span>
          </button>
        </div>

        <div class="link-row" v-if="state !== 'checking'">
          <p v-if="state === 'guest'">
            New to the platform? <NuxtLink to="/register">Join the community</NuxtLink>
          </p>
          <p v-else>
            Try again from <NuxtLink to="/login">login</NuxtLink>
          </p>
        </div>
      </div>
    </main>

    <div class="support-fab">
      <button type="button" aria-label="Support">
        <span class="icon">help_outline</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

import { computed, onMounted, ref } from 'vue'
import { navigateTo } from 'nuxt/app'
import { useSupabaseClient } from '#imports'

type ViewState = 'checking' | 'guest' | 'error'
const state = ref<ViewState>('checking')

const supabase = useSupabaseClient()

const routeByRole = (role?: string) => {
  if (role === 'advocate') return '/dashboard/advocate'
  if (role === 'verifier') return '/dashboard/verifier'
  return '/dashboard/worker'
}

const title = computed(() => {
  if (state.value === 'checking') return 'Preparing your workspace'
  if (state.value === 'guest') return 'Welcome to FairGig'
  return 'Something went wrong'
})

const subtitle = computed(() => {
  if (state.value === 'checking') return 'Checking your account session and role.'
  if (state.value === 'guest') return 'Please log in to continue to your dashboard.'
  return 'We could not verify your session automatically.'
})

const statusIcon = computed(() => {
  if (state.value === 'checking') return 'progress_activity'
  if (state.value === 'guest') return 'info'
  return 'error'
})

const statusText = computed(() => {
  if (state.value === 'checking') return 'Redirect in progress...'
  if (state.value === 'guest') return 'No active session found.'
  return 'Auto-redirect failed.'
})

const primaryLabel = computed(() => {
  if (state.value === 'checking') return 'Redirecting...'
  return 'Go to Login'
})

const primaryAction = async () => {
  if (state.value === 'checking') return
  await navigateTo('/login')
}

onMounted(async () => {
  try {
    const { data, error } = await supabase.auth.getSession()
    if (error) {
      state.value = 'error'
      return
    }

    const user = data.session?.user
    if (!user) {
      state.value = 'guest'
      return
    }

    const role = String(user.user_metadata?.role || 'worker')
    await navigateTo(routeByRole(role))
  } catch {
    state.value = 'error'
  }
})
</script>

<style scoped>
.auth-index {
  display: flex;
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
  overflow: hidden;
}

/* Left */
.left-panel {
  display: none;
  width: 50%;
  position: relative;
  padding: 3rem;
  color: #f2f1ff;
  background:
    linear-gradient(rgba(5, 69, 239, 0.62), rgba(5, 69, 239, 0.62)),
    url('https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1600&q=80')
      center / cover no-repeat;
}

.left-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(1200px 500px at -10% -20%, rgba(255, 255, 255, 0.22), transparent 55%),
    radial-gradient(900px 500px at 120% 120%, rgba(0, 0, 0, 0.25), transparent 60%);
  mix-blend-mode: soft-light;
}

.left-content {
  position: relative;
  z-index: 2;
}

.logo {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.05em;
}

.hero-copy {
  margin-top: 10rem;
  max-width: 36rem;
}

.hero-copy h1 {
  font-size: 3.75rem;
  font-weight: 800;
  line-height: 1.1;
}

.hero-copy p {
  margin-top: 2rem;
  font-size: 1.125rem;
  line-height: 1.75;
  opacity: 0.82;
}

/* Right */
.right-panel {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.form-shell {
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

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.header p {
  margin-top: 0.5rem;
  color: var(--fg-muted);
}

.status-chip {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.95rem 1rem;
  border-radius: 1rem;
  background: var(--fg-surface);
  color: var(--fg-muted);
  border: 1px solid var(--fg-border);
  font-weight: 600;
}

.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.actions {
  padding-top: 1rem;
  display: flex;
  justify-content: center;
}

/* ✅ Primary button microinteraction synced with login/register */
.primary-button {
  width: 18rem;
  height: 3.2rem;
  padding: 0 1.25rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  border: none;
  border-radius: 9999px;
  background: var(--fg-primary);
  color: #f2f1ff;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;

  transition:
    width 170ms cubic-bezier(0.2, 0.8, 0.2, 1),
    height 170ms cubic-bezier(0.2, 0.8, 0.2, 1),
    border-radius 170ms cubic-bezier(0.2, 0.8, 0.2, 1),
    background-color 120ms linear,
    box-shadow 140ms ease;

  box-shadow: var(--fg-shadow);
}

.primary-button:not(:disabled):hover {
  width: 20.5rem;
  height: 2.9rem;
  border-radius: 1rem;
  filter: brightness(0.95);
  box-shadow: var(--fg-shadow);
}

.primary-button:not(:disabled):active {
  filter: brightness(0.9);
}

.primary-button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 25%, transparent);
}

.primary-button.is-loading,
.primary-button:disabled {
  cursor: not-allowed;
  width: 18rem;
  height: 3.2rem;
  border-radius: 9999px;
  background: var(--fg-muted);
  box-shadow: var(--fg-shadow);
}

.link-row {
  margin-top: 2rem;
  text-align: center;
}

.link-row p {
  color: var(--fg-muted);
  font-size: 0.875rem;
}

.link-row a {
  color: var(--fg-primary);
  font-weight: 700;
  text-decoration: none;
  margin-left: 0.25rem;
}
.link-row a:hover {
  text-decoration: underline;
}

.support-fab {
  position: fixed;
  right: 2rem;
  bottom: 2rem;
  z-index: 30;
}

.support-fab button {
  width: 3.5rem;
  height: 3.5rem;
  border: 1px solid var(--fg-border);
  border-radius: 9999px;
  background: var(--fg-surface);
  color: var(--fg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--fg-shadow);
  cursor: pointer;
}

/* Responsive */
@media (max-width: 480px) {
  .primary-button,
  .primary-button.is-loading,
  .primary-button:disabled {
    width: min(18rem, 92vw);
  }

  .primary-button:not(:disabled):hover {
    width: min(20.5rem, 96vw);
  }
}

@media (prefers-reduced-motion: reduce) {
  .primary-button {
    transition: background-color 120ms linear, box-shadow 120ms ease, border-radius 120ms ease;
  }
}

@media (min-width: 1024px) {
  .left-panel {
    display: block;
  }

  .right-panel {
    width: 50%;
  }

  .mobile-logo {
    display: none;
  }

  .header {
    text-align: left;
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
  display: inline-block;
  white-space: nowrap;
  direction: ltr;
  font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}
</style>