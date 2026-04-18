<template>
  <div class="auth-bridge-container">
    <section class="left-section">
      <div class="content">
        <div class="logo">FairGig</div>
        <div class="main-text">
          <h1>Preparing your FairGig workspace.</h1>
          <p>
            We’re checking your session and routing you to the right dashboard with secure access.
          </p>
        </div>
      </div>
    </section>

    <main class="right-section">
      <div class="card">
        <div class="mobile-logo">FairGig</div>
        <h2>Just a moment...</h2>
        <p v-if="message">{{ message }}</p>

        <div class="loader-wrap" aria-live="polite">
          <div class="loader"></div>
        </div>

        <button class="primary-button" :disabled="isRedirecting">
          <span>{{ isRedirecting ? 'Redirecting...' : 'Continue' }}</span>
        </button>

        <div class="manual-links">
          <NuxtLink to="/login">Go to Login</NuxtLink>
          <NuxtLink to="/register">Create Account</NuxtLink>
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
import { ref, onMounted } from 'vue'
import { navigateTo } from 'nuxt/app'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const isRedirecting = ref(true)
const message = ref('Validating your account session...')

const resolveTargetByRole = (role: string) => {
  if (role === 'advocate') return '/dashboard/advocate'
  if (role === 'verifier') return '/dashboard/verifier'
  return '/dashboard/worker'
}

onMounted(async () => {
  try {
    const user = authStore.user
    if (!user) {
      message.value = 'No active session found. Please log in to continue.'
      isRedirecting.value = false
      return
    }

    const role = authStore.role
    message.value = `Signed in successfully. Redirecting to your ${role} dashboard...`
    await navigateTo(resolveTargetByRole(role))
  } catch {
    message.value = 'We could not complete auto-redirect. Please continue manually.'
    isRedirecting.value = false
  }
})
</script>

<style scoped>
.auth-bridge-container {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
  background-color: #f5f7f9;
  color: #2c2f31;
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

.card {
  width: 100%;
  max-width: 28rem;
  background: #ffffff;
  border-radius: 1.25rem;
  padding: 2rem;
  box-shadow: 0 20px 40px -24px rgba(44, 47, 49, 0.2);
  text-align: center;
}

.mobile-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
  font-size: 1.5rem;
  font-weight: 800;
  color: #0545ef;
  letter-spacing: -0.05em;
}

.card h2 {
  font-size: 1.875rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.card p {
  margin-top: 0.5rem;
  color: #595c5e;
}

.loader-wrap {
  margin: 1.5rem 0;
  display: flex;
  justify-content: center;
}
.loader {
  width: 2rem;
  height: 2rem;
  border-radius: 9999px;
  border: 3px solid #d9dde0;
  border-top-color: #0545ef;
  animation: spin 0.9s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.primary-button {
  width: 18rem;
  height: 3.2rem;
  margin: 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #595c5e;
  color: #f2f1ff;
  border: none;
  border-radius: 9999px;
  font-weight: 700;
  font-size: 1rem;
  cursor: not-allowed;
  box-shadow: 0 12px 18px -10px rgba(44, 47, 49, 0.25);
}

.manual-links {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
  gap: 1rem;
}
.manual-links a {
  color: #0545ef;
  font-weight: 700;
  text-decoration: none;
}
.manual-links a:hover {
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
  background-color: #ffffff;
  box-shadow: 0 24px 24px -4px rgba(44, 47, 49, 0.12);
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0545ef;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
}
.support-fab button:hover {
  background-color: #0545ef;
  color: #f2f1ff;
}
.support-fab .icon {
  font-size: 1.5rem;
  transition: transform 0.3s;
}
.support-fab button:hover .icon {
  transform: scale(1.1);
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