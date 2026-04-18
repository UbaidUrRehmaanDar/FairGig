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
import { ref } from 'vue'

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const acceptedTerms = ref(false)

const isRegistering = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const errors = ref<{
  fullName: string
  email: string
  password: string
  confirmPassword: string
  terms: string
}>({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  terms: ''
})

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

const toggleShowPassword = () => {
  showPassword.value = !showPassword.value
}

const toggleShowConfirmPassword = () => {
  showConfirmPassword.value = !showConfirmPassword.value
}

const validateForm = () => {
  errors.value.fullName = ''
  errors.value.email = ''
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
    !errors.value.password &&
    !errors.value.confirmPassword &&
    !errors.value.terms
  )
}

const handleRegister = async () => {
  if (isRegistering.value) return

  if (!validateForm()) return

  isRegistering.value = true
  try {
    await sleep(1200)
    // TODO: integrate real registration API here
  } finally {
    isRegistering.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
  background-color: #f5f7f9;
  color: #2c2f31;
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
  border: 2px solid #0545ef;
  object-fit: cover;
  margin-left: 0.75rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
  background: #c9d4ff;
}

.avatar-plus {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  border: 2px solid #0545ef;
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
}

.mobile-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: #0545ef;
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
  color: #595c5e;
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
  color: #595c5e;
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
  color: #abadaf;
  font-size: 1.25rem;
  transition: color 0.2s;
}

.input-with-icon:focus-within .icon {
  color: #0545ef;
}

.input-with-icon input {
  width: 100%;
  padding: 1rem 3.25rem 1rem 3rem;
  background-color: #eef1f3;
  border: none;
  border-radius: 1rem;
  color: #2c2f31;
  outline: none;
  transition: box-shadow 0.2s, background-color 0.2s;
}

.input-with-icon input:focus {
  box-shadow: 0 0 0 2px rgba(5, 69, 239, 0.2);
  background-color: #ffffff;
}

.input-with-icon input[aria-invalid='true'] {
  box-shadow: 0 0 0 2px rgba(217, 45, 32, 0.2);
  background-color: #fff6f6;
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
  color: #595c5e;
  background: rgba(171, 173, 175, 0.12);
}

.field-error {
  margin-top: 0.25rem;
  margin-left: 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #d92d20;
  line-height: 1.2;
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
  background-color: #d9dde0;
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
  background-color: #fff;
  border-radius: 50%;
  transition: 0.25s ease;
}

.switch input:checked + .slider {
  background-color: #0545ef;
}

.switch input:checked + .slider::before {
  transform: translateX(1.25rem);
}

.switch input:focus-visible + .slider {
  box-shadow: 0 0 0 3px rgba(5, 69, 239, 0.25);
}


.terms-row label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #595c5e;
  line-height: 1.35;
  cursor: pointer;
  margin: 0;
}

.terms-row a {
  color: #0545ef;
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
  background-color: #d9dde0;
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
  background-color: #fff;
  border-radius: 50%;
  transition: 0.25s ease;
}

.toggle-switch input:checked + .slider {
  background-color: #0545ef;
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
  background-color: #0545ef;
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
  box-shadow: 0 12px 24px -8px rgba(5, 69, 239, 0.3);
}

.primary-button:not(:disabled):hover {
  width: 20.5rem;
  height: 2.9rem;
  border-radius: 1rem;
  background-color: #003bd4;
  box-shadow: 0 16px 28px -10px rgba(5, 69, 239, 0.35);
}

.primary-button:not(:disabled):active {
  background-color: #0033bb;
}

.primary-button:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px rgba(5, 69, 239, 0.25),
    0 16px 28px -10px rgba(5, 69, 239, 0.35);
}

.primary-button.is-loading,
.primary-button:disabled {
  cursor: not-allowed;
  width: 18rem;
  height: 3.2rem;
  border-radius: 9999px;
  background-color: #595c5e;
  box-shadow: 0 12px 18px -10px rgba(44, 47, 49, 0.25);
}

.login-link {
  margin-top: 3rem;
  text-align: center;
}

.login-link p {
  color: #595c5e;
  font-size: 0.875rem;
}

.login-link a {
  color: #0545ef;
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
  background-color: #fff;
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