<template>
  <div class="login-container">
    <!-- Left Column: Editorial/Branded Section -->
    <section class="left-section">
      <div class="content">
        <div class="logo">FairGig</div>
        <div class="main-text">
          <h1>Welcome back to FairGig.</h1>
          <p>
            Empowering the future of independent work with fair pay, better benefits, and total
            transparency.
          </p>
        </div>

        <div class="social-proof">
          <div class="avatars" aria-hidden="true">
            <img
              class="avatar-photo"
              src="https://picsum.photos/seed/sea1/80/80"
              alt="Community member profile photo"
            />
            <img
              class="avatar-photo"
              src="https://picsum.photos/seed/flower2/80/80"
              alt="Community member profile photo"
            />
            <img
              class="avatar-photo"
              src="https://picsum.photos/seed/mountain3/80/80"
              alt="Community member profile photo"
            />
            <div class="avatar-plus">+2k</div>
          </div>
          <p>Joined by 2,000+ gig professionals this week.</p>
        </div>
      </div>
    </section>

    <!-- Right Column: Login Form Section -->
    <main class="right-section">
      <div class="form-container">
        <div class="mobile-logo">FairGig</div>

        <button
          type="button"
          class="theme-toggle"
          :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="toggleTheme"
        >
          <span class="icon">{{ isDark ? 'light_mode' : 'dark_mode' }}</span>
        </button>

        <div class="form-header">
          <h2>Access Secure Portal</h2>
          <p>Please enter your credentials to continue.</p>
        </div>

        <form class="login-form" novalidate @submit.prevent="handleLogin">
          <div class="input-group">
            <label for="email">Email Address</label>
            <div class="input-with-icon">
              <span class="icon">email</span>
              <input
                id="email"
                v-model.trim="email"
                type="email"
                :aria-invalid="!!errors.email"
                aria-describedby="email-error"
              />
            </div>
            <p v-if="errors.email" id="email-error" class="field-error">{{ errors.email }}</p>
          </div>

          <div class="input-group">
            <div class="label-container">
              <label for="password">Password</label>
              <a href="#">Forgot Password?</a>
            </div>

            <div class="input-with-icon">
              <span class="icon">lock</span>
              <input
                id="password"
                v-model.trim="password"
                :type="showPassword ? 'text' : 'password'"
                :aria-invalid="!!errors.password"
                aria-describedby="password-error"
              />

              <button
                type="button"
                class="icon-button"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                @click="toggleShowPassword"
              >
                <span class="icon">{{ showPassword ? 'visibility_off' : 'visibility' }}</span>
              </button>
            </div>
            <p v-if="errors.password" id="password-error" class="field-error">
              {{ errors.password }}
            </p>
          </div>

<div class="remember-me">
  <label class="switch" for="remember-device">
    <input id="remember-device" v-model="rememberDevice" type="checkbox" />
    <span class="slider"></span>
  </label>
  <label class="remember-label" for="remember-device">Remember device</label>
</div>
          <div class="actions">
            <button
              type="submit"
              class="primary-button"
              :class="{ 'is-loading': isLoggingIn }"
              :disabled="isLoggingIn"
            >
              <span v-if="!isLoggingIn">Login</span>
              <span v-else>Authenticating...</span>
            </button>
          </div>
        </form>

        <div class="signup-link">
          <p>New to the platform? <a href="/register">Join the community</a></p>
        </div>
      </div>
    </main>

  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { User } from '@supabase/supabase-js'
import { navigateTo } from 'nuxt/app'
import { useSupabaseClient } from '#imports'

const supabase = useSupabaseClient()

const email = ref('')
const password = ref('')
const rememberDevice = ref(false)
const isLoggingIn = ref(false)
const showPassword = ref(false)
const isDark = ref(false)

const errors = ref<{ email: string; password: string }>({
  email: '',
  password: ''
})

const toggleShowPassword = () => {
  showPassword.value = !showPassword.value
}

const applyTheme = (mode: 'light' | 'dark') => {
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle('dark', mode === 'dark')
  localStorage.setItem('fg_theme', mode)
  isDark.value = mode === 'dark'
}

const toggleTheme = () => {
  applyTheme(isDark.value ? 'light' : 'dark')
}

const validateForm = () => {
  errors.value.email = ''
  errors.value.password = ''

  if (!email.value) {
    errors.value.email = 'Email is required.'
  } else {
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)
    if (!emailOk) errors.value.email = 'Please enter a valid email address.'
  }

  if (!password.value) {
    errors.value.password = 'Password is required.'
  }

  return !errors.value.email && !errors.value.password
}

const resolveTargetByRole = (role: string) => {
  if (role === 'advocate') return '/dashboard/advocate'
  if (role === 'verifier') return '/dashboard/verifier'
  return '/dashboard/worker'
}

const resolveRole = (user: User | null) => {
  const roleCandidate =
    (typeof user?.user_metadata?.role === 'string' && user.user_metadata.role) ||
    (typeof user?.app_metadata?.role === 'string' && user.app_metadata.role) ||
    'worker'

  return String(roleCandidate).toLowerCase().trim()
}

const handleLogin = async () => {
  if (isLoggingIn.value) return
  if (!validateForm()) return

  isLoggingIn.value = true
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email.value,
      password: password.value
    })

    if (error) {
      errors.value.password = error.message || 'Login failed. Please check your credentials.'
      return
    }

    const role = resolveRole(data.user)
    await navigateTo(resolveTargetByRole(role))
    if (!rememberDevice.value) {
      // Session persistence is controlled by the Supabase client configuration.
      // Keeping this toggle for UX, but it won't change persistence without client config.
    }
  } catch (e: any) {
    errors.value.password = e?.message || 'Login failed. Please check your credentials.'
  } finally {
    isLoggingIn.value = false
  }
}

onMounted(async () => {
  const savedTheme = localStorage.getItem('fg_theme')
  if (savedTheme === 'dark' || savedTheme === 'light') {
    applyTheme(savedTheme)
  } else {
    isDark.value = document.documentElement.classList.contains('dark')
  }

  const { data } = await supabase.auth.getSession()
  if (data.session?.user) {
    await navigateTo(resolveTargetByRole(resolveRole(data.session.user)))
  }
})
</script>

<style scoped>
/* General Styles */
.login-container {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
  background-color: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
}

/* Left Section */
.left-section {
  display: none;
  width: 50%;
  position: relative;
  flex-direction: column;
  justify-content: space-between;
  padding: 3rem;
  color: #f2f1ff;
  overflow: hidden;

  /* image + dark fallback */
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

.left-section::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(
    to bottom,
    rgba(3, 29, 120, 0.25) 0%,
    rgba(3, 29, 120, 0.08) 45%,
    rgba(2, 18, 72, 0.35) 100%
  );
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
  margin-bottom: 3rem;
  margin-top: 10rem;
}

.left-section h1 {
  font-size: 3.75rem;
  font-weight: 800;
  line-height: 1.1;
  max-width: 36rem;
}

.left-section p {
  margin-top: 2rem;
  font-size: 1.125rem;
  max-width: 32rem;
  line-height: 1.75;
  opacity: 0.8;
}

.social-proof {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.avatars {
  display: flex;
  margin-left: -0.75rem;
  align-items: center;
}

.avatar-photo {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  border: 2px solid var(--fg-primary);
  object-fit: cover;
  margin-left: 0.75rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
  background: #c9d4ff;
}

.avatar-plus {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  border: 2px solid var(--fg-primary);
  background-color: #859aff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  font-weight: 700;
  color: #001867;
  margin-left: 0.75rem;
}

.social-proof p {
  font-size: 0.875rem;
  font-weight: 500;
  opacity: 0.6;
}

/* Right Section */
.right-section {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  overflow-y: auto;
}

.form-container {
  width: 100%;
  max-width: 28rem;
  position: relative;
}

.theme-toggle {
  position: absolute;
  top: 0;
  right: 0;
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 9999px;
  border: 1px solid var(--fg-border);
  background: var(--fg-surface);
  color: var(--fg-text);
  box-shadow: var(--fg-shadow);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 120ms linear, transform 170ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.theme-toggle:hover {
  background: var(--fg-surface-muted);
  transform: translateY(-1px);
}

.theme-toggle:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--fg-primary) 20%, transparent),
    var(--fg-shadow);
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
  margin-bottom: 2.5rem;
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

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--fg-muted);
  margin-left: 0.25rem;
}

.label-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 0.25rem;
}

.label-container a {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--fg-primary);
  text-decoration: none;
}
.label-container a:hover {
  text-decoration: underline;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-icon .icon {
  position: absolute;
  left: 1rem;
  pointer-events: none;
  color: var(--fg-muted);
  font-size: 1.25rem;
  transition: color 0.2s;
}

.input-with-icon:focus-within .icon {
  color: var(--fg-primary);
}

.input-with-icon input {
  width: 100%;
  padding: 1rem 3.25rem 1rem 3rem;
  background-color: var(--fg-surface-muted);
  border: none;
  border-radius: 1rem;
  color: var(--fg-text);
  outline: none;
  transition: box-shadow 0.2s, background-color 0.2s;
}

.input-with-icon input::placeholder {
  color: var(--fg-placeholder-color);
}

.input-with-icon input:focus {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 20%, transparent);
  background-color: var(--fg-surface);
}

.input-with-icon input[aria-invalid='true'] {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-danger) 20%, transparent);
  background-color: color-mix(in srgb, var(--fg-danger) 10%, var(--fg-surface));
}

.field-error {
  margin-top: 0.25rem;
  margin-left: 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--fg-danger);
  line-height: 1.2;
}

.icon-button {
  position: absolute;
  right: 0.9rem;
  width: 2.25rem;
  height: 2.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #abadaf;
}
.icon-button:hover {
  color: var(--fg-muted);
  background: rgba(171, 173, 175, 0.12);
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 0.25rem;
}

.switch {
  position: relative;
  width: 2.5rem;
  height: 1.25rem;
  display: inline-block;
  flex: 0 0 auto;
}

.switch input {
  position: absolute;
  opacity: 0;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  cursor: pointer;
}

.switch .slider {
  position: absolute;
  inset: 0;
  background-color: var(--fg-border);
  border-radius: 9999px;
  transition: 0.25s ease;
  pointer-events: none;
}

.switch .slider::before {
  content: '';
  position: absolute;
  width: 1rem;
  height: 1rem;
  left: 2px;
  top: 2px;
  border-radius: 50%;
  background-color: var(--fg-surface);
  transition: 0.25s ease;
}

.switch input:checked + .slider {
  background-color: var(--fg-primary);
}

.switch input:checked + .slider::before {
  transform: translateX(1.25rem);
}

.switch input:focus-visible + .slider {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--fg-primary) 25%, transparent);
}

.remember-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--fg-muted);
  margin: 0;
  cursor: pointer;
}


.remember-me label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--fg-muted);
  margin: 0;
  cursor: pointer;
}


.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--fg-border);
  border-radius: 9999px;
  transition: 0.25s ease;
}

.slider:before {
  position: absolute;
  content: '';
  height: 1rem;
  width: 1rem;
  left: 2px;
  bottom: 2px;
  background-color: var(--fg-surface);
  border-radius: 50%;
  transition: 0.25s ease;
}


.actions {
  padding-top: 1rem;
  display: flex;
  justify-content: center;
}

.primary-button {
  width: 18rem;
  height: 3.2rem;
  padding: 0 1.25rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  background-color: var(--fg-primary);
  color: #f2f1ff;
  border: none;
  border-radius: 9999px;
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
  background-color: var(--fg-muted);
  box-shadow: var(--fg-shadow);
}

@media (prefers-reduced-motion: reduce) {
  .primary-button {
    transition: background-color 120ms linear, box-shadow 120ms ease, border-radius 120ms ease;
  }
}

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

.signup-link {
  margin-top: 3rem;
  text-align: center;
}

.signup-link p {
  color: var(--fg-muted);
  font-size: 0.875rem;
}

.signup-link a {
  color: var(--fg-primary);
  font-weight: 700;
  text-decoration: none;
  margin-left: 0.25rem;
}
.signup-link a:hover {
  text-decoration: underline;
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

/* ===== Mobile compatibility patch ===== */
@media (max-width: 1023px) {
  .login-container {
    min-height: 100dvh;
  }

  .right-section {
    width: 100%;
    align-items: flex-start;
    padding: 1rem;
  }

  .form-container {
    max-width: 100%;
    margin: 0 auto;
  }

  .mobile-logo {
    margin-bottom: 1.5rem;
  }

  .theme-toggle {
    top: 0.25rem;
    right: 0.25rem;
  }

  .form-header {
    margin-bottom: 1.4rem;
  }

  .form-header h2 {
    font-size: clamp(1.45rem, 5vw, 1.875rem);
    line-height: 1.2;
  }

  .form-header p {
    font-size: 0.92rem;
  }

  .login-form {
    gap: 1rem;
  }

  .input-with-icon input {
    min-height: 3rem;
    font-size: 16px; /* prevents iOS zoom-on-focus */
  }

  .label-container {
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .label-container a {
    margin-left: auto;
  }

  .remember-me {
    padding: 0;
  }

  .actions {
    padding-top: 0.75rem;
  }

  .signup-link {
    margin-top: 1.5rem;
    padding-bottom: 0.25rem;
  }

}

@media (max-width: 480px) {
  .right-section {
    padding: 0.9rem 0.85rem;
  }

  .form-header {
    margin-bottom: 1.25rem;
  }

  .primary-button,
  .primary-button.is-loading,
  .primary-button:disabled {
    width: 100%;
    max-width: 100%;
  }

  /* keep your hover philosophy but avoid overflow on tiny screens */
  .primary-button:not(:disabled):hover {
    width: 100%;
    height: 3rem;
    border-radius: 1rem;
  }
}

/* Optional: avoid any hover-only jitter on touch devices */
@media (hover: none) and (pointer: coarse) {
  .primary-button:not(:disabled):hover {
    width: 100%;
    height: 3.2rem;
    border-radius: 9999px;
    filter: none;
  }

}
</style>