<template>
  <div class="register-container">
    <!-- Left Column: Editorial/Branded Section -->
    <section class="left-section">
      <div class="content">
        <div class="logo">FairGig</div>

        <div class="main-text">
          <h1>Build your FairGig profile.</h1>
          <p>
            Join a platform designed for independent workers with fair pay, practical benefits,
            and total transparency.
          </p>
        </div>

        <div class="social-proof">
          <div class="avatars" aria-hidden="true">
            <img
              class="avatar-photo"
              src="https://picsum.photos/seed/sea-register-1/80/80"
              alt="Community member profile photo"
            />
            <img
              class="avatar-photo"
              src="https://picsum.photos/seed/flower-register-2/80/80"
              alt="Community member profile photo"
            />
            <img
              class="avatar-photo"
              src="https://picsum.photos/seed/mountain-register-3/80/80"
              alt="Community member profile photo"
            />
            <div class="avatar-plus">+10k</div>
          </div>
          <p>Trusted by 10,000+ gig professionals and partners.</p>
        </div>
      </div>
    </section>

    <!-- Right Column: Register Form Section -->
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
          <h2>Create your account</h2>
          <p>Set up your profile to get started.</p>
        </div>

        <form class="register-form" novalidate @submit.prevent="handleRegister">
          <div class="input-group">
            <label for="full_name">Full Name</label>
            <div class="input-with-icon">
              <span class="icon">person</span>
              <input
                id="full_name"
                v-model.trim="fullName"
                type="text"
                :aria-invalid="!!errors.fullName"
                aria-describedby="full-name-error"
              />
            </div>
            <p v-if="errors.fullName" id="full-name-error" class="field-error">
              {{ errors.fullName }}
            </p>
          </div>

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
            <label for="role">Role</label>
            <div class="input-with-icon">
              <span class="icon">badge</span>
              <select
                id="role"
                v-model="selectedRole"
                :aria-invalid="!!errors.role"
                aria-describedby="role-error"
              >
                <option value="worker">Worker</option>
                <option value="verifier">Verifier</option>
                <option value="advocate">Advocate</option>
              </select>
            </div>
            <p v-if="errors.role" id="role-error" class="field-error">{{ errors.role }}</p>
          </div>

          <div class="password-grid">
            <div class="input-group">
              <label for="password">Password</label>
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

            <div class="input-group">
              <label for="confirm_password">Confirm Password</label>
              <div class="input-with-icon">
                <span class="icon">verified_user</span>
                <input
                  id="confirm_password"
                  v-model.trim="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  :aria-invalid="!!errors.confirmPassword"
                  aria-describedby="confirm-password-error"
                />
                <button
                  type="button"
                  class="icon-button"
                  :aria-label="showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'"
                  @click="toggleShowConfirmPassword"
                >
                  <span class="icon">{{
                    showConfirmPassword ? 'visibility_off' : 'visibility'
                  }}</span>
                </button>
              </div>
              <p v-if="errors.confirmPassword" id="confirm-password-error" class="field-error">
                {{ errors.confirmPassword }}
              </p>
            </div>
          </div>

          <div class="terms-row">
  <label class="switch" for="terms">
    <input id="terms" v-model="acceptedTerms" type="checkbox" />
    <span class="slider"></span>
  </label>

  <label class="terms-label" for="terms">
    I agree to the <a href="#">Terms & Conditions</a> and <a href="#">Privacy Policy</a>.
  </label>
</div>
<p v-if="errors.terms" class="field-error terms-error">{{ errors.terms }}</p>

          <p v-if="statusMessage" :class="['form-message', statusType]">{{ statusMessage }}</p>

          <div class="actions">
            <button
              type="submit"
              class="primary-button"
              :class="{ 'is-loading': isRegistering }"
              :disabled="isRegistering"
            >
              <span v-if="!isRegistering">Create Account</span>
              <span v-else>Creating Account...</span>
            </button>
          </div>
        </form>

        <div class="login-link">
          <p>Already have an account? <a href="/login">Log in instead</a></p>
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
import { onMounted, ref } from 'vue'
import { navigateTo } from 'nuxt/app'
import { useSupabaseClient } from '#imports'
import { useApi } from '../composables/useApi'

const supabase = useSupabaseClient()
const { authFetch } = useApi()

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const selectedRole = ref<'worker' | 'verifier' | 'advocate'>('worker')
const acceptedTerms = ref(false)

const isRegistering = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const statusMessage = ref('')
const statusType = ref<'error' | 'success'>('error')
const isDark = ref(false)

const errors = ref<{
  fullName: string
  email: string
  role: string
  password: string
  confirmPassword: string
  terms: string
}>({
  fullName: '',
  email: '',
  role: '',
  password: '',
  confirmPassword: '',
  terms: ''
})

const roleToPath = (role: string) => {
  if (role === 'advocate') return '/dashboard/advocate'
  if (role === 'verifier') return '/dashboard/verifier'
  return '/dashboard/worker'
}

const resolveRole = (user: any): 'worker' | 'verifier' | 'advocate' => {
  const roleCandidate =
    (typeof user?.user_metadata?.role === 'string' && user.user_metadata.role) ||
    (typeof user?.app_metadata?.role === 'string' && user.app_metadata.role) ||
    selectedRole.value

  const normalized = String(roleCandidate || '').trim().toLowerCase()
  if (normalized === 'advocate') return 'advocate'
  if (normalized === 'verifier') return 'verifier'
  return 'worker'
}

const toggleShowPassword = () => {
  showPassword.value = !showPassword.value
}

const toggleShowConfirmPassword = () => {
  showConfirmPassword.value = !showConfirmPassword.value
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
  errors.value.fullName = ''
  errors.value.email = ''
  errors.value.role = ''
  errors.value.password = ''
  errors.value.confirmPassword = ''
  errors.value.terms = ''

  if (!fullName.value) {
    errors.value.fullName = 'Full name is required.'
  }

  if (!email.value) {
    errors.value.email = 'Email is required.'
  } else {
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)
    if (!emailOk) errors.value.email = 'Please enter a valid email address.'
  }

  if (!password.value) {
    errors.value.password = 'Password is required.'
  } else if (password.value.length < 8) {
    errors.value.password = 'Password must be at least 8 characters.'
  }

  if (!['worker', 'verifier', 'advocate'].includes(selectedRole.value)) {
    errors.value.role = 'Please choose a valid role.'
  }

  if (!confirmPassword.value) {
    errors.value.confirmPassword = 'Please confirm your password.'
  } else if (confirmPassword.value !== password.value) {
    errors.value.confirmPassword = 'Passwords do not match.'
  }

  if (!acceptedTerms.value) {
    errors.value.terms = 'You must accept Terms & Conditions to continue.'
  }

  return (
    !errors.value.fullName &&
    !errors.value.email &&
    !errors.value.role &&
    !errors.value.password &&
    !errors.value.confirmPassword &&
    !errors.value.terms
  )
}

const isRateLimitError = (error: any) => {
  const status = Number(error?.status || 0)
  const message = String(error?.message || '').toLowerCase()
  const code = String(error?.code || '').toLowerCase()

  return (
    status === 429 ||
    message.includes('rate limit') ||
    message.includes('too many requests') ||
    code.includes('rate_limit') ||
    code.includes('over_email_send_rate_limit')
  )
}

const isAlreadyRegisteredError = (error: any) => {
  const message = String(error?.message || '').toLowerCase()
  const code = String(error?.code || '').toLowerCase()

  return (
    (message.includes('already') && message.includes('registered')) ||
    code.includes('email_exists') ||
    code.includes('user_already_exists')
  )
}

const fallbackNameFromEmail = (emailValue: string) => {
  const localPart = String(emailValue || '').split('@')[0] || 'Worker'
  return localPart
    .replace(/[._-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

const ensureProfile = async (role: 'worker' | 'verifier' | 'advocate') => {
  const normalizedName =
    String(fullName.value || '').trim() || fallbackNameFromEmail(String(email.value || '').trim())

  try {
    await authFetch('/auth/setup-profile', {
      method: 'POST',
      body: JSON.stringify({
        full_name: normalizedName,
        city_zone: 'Unknown',
        platform_category: 'ride_hailing',
        role
      })
    })
  } catch {
    // Do not block auth flow if profile bootstrap fails; user can retry later.
  }
}

const handleRegister = async () => {
  if (isRegistering.value) return

  statusMessage.value = ''
  if (!validateForm()) return

  isRegistering.value = true
  try {
    const { data, error } = await supabase.auth.signUp({
      email: email.value.toLowerCase(),
      password: password.value,
      options: {
        data: {
          full_name: fullName.value,
          role: selectedRole.value
        },
        emailRedirectTo: typeof window !== 'undefined' ? `${window.location.origin}/confirm` : undefined
      }
    })

    if (error) {
      if (isRateLimitError(error) || isAlreadyRegisteredError(error)) {
        // If signup is rate-limited but account already exists, try signing in directly.
        const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
          email: email.value.toLowerCase(),
          password: password.value
        })

        if (!signInError && signInData.user) {
          const role = resolveRole(signInData.user)
          await ensureProfile(role)
          statusType.value = 'success'
          statusMessage.value = 'Account already exists. Signed in successfully.'
          await navigateTo(roleToPath(role))
          return
        }

        const signInMessage = String(signInError?.message || '').toLowerCase()
        if (signInMessage.includes('email not confirmed')) {
          statusType.value = 'error'
          statusMessage.value =
            'Your account exists but is not confirmed yet. Check your inbox and try logging in after confirmation.'
          return
        }

        statusType.value = 'error'
        statusMessage.value =
          'Email sending is temporarily rate-limited. Wait a minute and try again, or use Log in if your account already exists.'
        return
      }

      statusType.value = 'error'
      statusMessage.value = error.message || 'Registration failed. Please try again.'
      return
    }

    statusType.value = 'success'

    if (data.session?.user) {
      const role = resolveRole(data.session.user)
      await ensureProfile(role)
      statusMessage.value = 'Account created successfully.'
      await navigateTo(roleToPath(role))
      return
    }

    statusMessage.value = 'Account created. Check your email to confirm, then sign in.'
    await navigateTo('/confirm')
  } catch (error: any) {
    statusType.value = 'error'
    statusMessage.value = error?.message || 'Registration failed. Please try again.'
  } finally {
    isRegistering.value = false
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
    await navigateTo(roleToPath(resolveRole(data.session.user)))
  }
})
</script>

<style scoped>
.register-container {
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
  opacity: 0.75;
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

.register-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.password-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
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

.input-with-icon select {
  width: 100%;
  padding: 1rem 3.25rem 1rem 3rem;
  background-color: var(--fg-surface-muted);
  border: none;
  border-radius: 1rem;
  color: var(--fg-text);
  outline: none;
  transition: box-shadow 0.2s, background-color 0.2s;
  appearance: none;
}

.input-with-icon input:focus {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 20%, transparent);
  background-color: var(--fg-surface);
}

.input-with-icon select:focus {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 20%, transparent);
  background-color: var(--fg-surface);
}

.input-with-icon input[aria-invalid='true'] {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-danger) 20%, transparent);
  background-color: color-mix(in srgb, var(--fg-danger) 10%, var(--fg-surface));
}

.input-with-icon select[aria-invalid='true'] {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-danger) 20%, transparent);
  background-color: color-mix(in srgb, var(--fg-danger) 10%, var(--fg-surface));
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

.field-error {
  margin-top: 0.25rem;
  margin-left: 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--fg-danger);
  line-height: 1.2;
}

.form-message {
  margin-top: -0.25rem;
  margin-left: 0.25rem;
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.25;
}

.form-message.error {
  color: var(--fg-danger);
}

.form-message.success {
  color: var(--fg-success);
}

.terms-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0 0.25rem;
}

.switch {
  position: relative;
  width: 2.5rem;
  height: 1.25rem;
  display: inline-block;
  flex: 0 0 auto;
  margin-top: 0.1rem;
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
  height: 1rem;
  width: 1rem;
  left: 2px;
  top: 2px;
  background-color: var(--fg-surface);
  border-radius: 50%;
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


.terms-row label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--fg-muted);
  line-height: 1.35;
  cursor: pointer;
  margin: 0;
}

terms-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--fg-muted);
  line-height: 1.35;
  cursor: pointer;
  margin: 0;
}

.terms-label a {
  color: var(--fg-primary);
  font-weight: 700;
  text-decoration: none;
}
.terms-label a:hover {
  text-decoration: underline;
}

.terms-error {
  margin-top: -0.5rem;
}

.terms-row a {
  color: var(--fg-primary);
  font-weight: 700;
  text-decoration: none;
}
.terms-row a:hover {
  text-decoration: underline;
}

.terms-error {
  margin-top: -0.5rem;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 2.5rem;
  height: 1.25rem;
  margin-top: 0.1rem;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
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

.toggle-switch input:checked + .slider {
  background-color: var(--fg-primary);
}

.toggle-switch input:checked + .slider:before {
  transform: translateX(1.25rem);
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

.login-link {
  margin-top: 3rem;
  text-align: center;
}

.login-link p {
  color: var(--fg-muted);
  font-size: 0.875rem;
}

.login-link a {
  color: var(--fg-primary);
  font-weight: 700;
  text-decoration: none;
  margin-left: 0.25rem;
}
.login-link a:hover {
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

.support-fab .icon {
  font-size: 1.5rem;
  transition: transform 0.3s;
}

.support-fab button:hover .icon {
  transform: scale(1.1);
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

@media (min-width: 768px) {
  .password-grid {
    grid-template-columns: 1fr 1fr;
  }
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
  word-wrap: normal;
  direction: ltr;
  font-feature-settings: 'liga';
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}
</style>