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
            <!-- Use proper, non-AI, simple avatar icons (inline SVG) -->
            <span class="avatar-icon" title="Professional">
              <svg viewBox="0 0 24 24" role="img" aria-label="Professional avatar">
                <path
                  d="M12 12.2c2.7 0 4.9-2.2 4.9-4.9S14.7 2.4 12 2.4 7.1 4.6 7.1 7.3s2.2 4.9 4.9 4.9Zm0 2.2c-4 0-7.5 2.2-9.2 5.5-.3.6.1 1.3.8 1.3h16.8c.7 0 1.1-.7.8-1.3-1.7-3.3-5.2-5.5-9.2-5.5Z"
                />
              </svg>
            </span>

            <span class="avatar-icon" title="Professional">
              <svg viewBox="0 0 24 24" role="img" aria-label="Professional avatar">
                <path
                  d="M12 12.2c2.7 0 4.9-2.2 4.9-4.9S14.7 2.4 12 2.4 7.1 4.6 7.1 7.3s2.2 4.9 4.9 4.9Zm0 2.2c-4 0-7.5 2.2-9.2 5.5-.3.6.1 1.3.8 1.3h16.8c.7 0 1.1-.7.8-1.3-1.7-3.3-5.2-5.5-9.2-5.5Z"
                />
              </svg>
            </span>

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

        <div class="form-header">
          <h2>Access Secure Portal</h2>
          <p>Please enter your credentials to continue.</p>
        </div>

        <form class="login-form" @submit.prevent="handleLogin">
          <div class="input-group">
            <label for="email">Email Address</label>
            <div class="input-with-icon">
              <span class="icon">email</span>
              <input id="email" v-model="email" type="email" required />
            </div>
          </div>

          <div class="input-group">
            <div class="label-container">
              <label for="password">Password</label>
              <a href="#">Forgot Password?</a>
            </div>

            <div class="input-with-icon">
              <span class="icon">lock</span>

              <!-- Keep the button visually *inside* the field by sharing the same wrapper + padding -->
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
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
          </div>

          <div class="remember-me">
            <div class="toggle-switch">
              <input type="checkbox" />
              <div class="slider"></div>
            </div>
            <span>Remember device</span>
          </div>

          <div class="actions">
            <button
              type="submit"
              class="primary-button"
              :class="{
                'is-hover': isHoveringLogin,
                'is-loading': isLoggingIn
              }"
              :disabled="isLoggingIn"
              @mouseenter="onLoginEnter"
              @mouseleave="onLoginLeave"
            >
              <span v-if="!isLoggingIn">Login</span>
              <span v-else>Authenticating...</span>
            </button>
          </div>
        </form>

        <div class="sso-divider">
          <div class="line"></div>
          <span>Or continue with</span>
          <div class="line"></div>
        </div>

        <div class="sso-buttons">
          <button>
            <img
              alt="Google logo icon"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBZraQLEja8plyQCCa5yetTP_cFOxzf64UdGJxy2XT6R6VAu77keVgRihM8FHV1Osq0mdrVHdssMNhC29ex1rVY3bLKI_QLLhZFIvxM1oEc_g2F7HXK38-zg8mbu6RrP_g0DzeP-M0TM6HESOBGKZN7go772_qXWcMQ2TB1BeeHvTUMkgt8FPMAcxu3ZMdSJt8rc5Xy-31S3zd5-09fpzaAp79aUGl7s5L0ngTIBpaTrWUjZ7iwMU8GASd_m_gkLTbc5jwVNLxpMJE"
            />
            <span>Google</span>
          </button>
          <button>
            <span class="icon">fingerprint</span>
            <span>Biometrics</span>
          </button>
        </div>

        <div class="signup-link">
          <p>New to the platform? <a href="/register">Join the community</a></p>
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

const email = ref('')
const password = ref('')
const isLoggingIn = ref(false)

const showPassword = ref(false)

const isHoveringLogin = ref(false)

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

const toggleShowPassword = () => {
  showPassword.value = !showPassword.value
}

const onLoginEnter = () => {
  if (!isLoggingIn.value) isHoveringLogin.value = true
}
const onLoginLeave = () => {
  isHoveringLogin.value = false
}

const handleLogin = async () => {
  if (isLoggingIn.value) return

  isLoggingIn.value = true
  try {
    await sleep(1200)
  } finally {
    isLoggingIn.value = false
    isHoveringLogin.value = false
  }
}
</script>

<style scoped>
/* General Styles */
.login-container {
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
  background-color: #0545ef;
  color: #f2f1ff;
  overflow: hidden;
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

.avatar-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  border: 2px solid #0545ef;
  background: rgba(255, 255, 255, 0.18);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 0.75rem; /* cancels the -0.75rem container shift visually */
}

.avatar-icon svg {
  width: 1.4rem;
  height: 1.4rem;
  fill: #f2f1ff;
  opacity: 0.95;
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
  color: #595c5e;
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
  color: #0545ef;
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
  color: #abadaf;
  font-size: 1.25rem;
  transition: color 0.2s;
}

.input-with-icon:focus-within .icon {
  color: #0545ef;
}

.input-with-icon input {
  width: 100%;
  /* Slightly more right padding so the eye button sits *inside* without overlapping text */
  padding: 1rem 3.25rem 1rem 3rem;
  background-color: #eef1f3;
  border: none;
  border-radius: 1rem;
  color: #2c2f31;
  outline: none;
  transition: box-shadow 0.2s, background-color 0.2s;
}

.input-with-icon input::placeholder {
  color: #abadaf;
}

.input-with-icon input:focus {
  box-shadow: 0 0 0 2px rgba(5, 69, 239, 0.2);
  background-color: #ffffff;
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

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 0.25rem;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 2.5rem;
  height: 1.25rem;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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
  background-color: white;
  border-radius: 50%;
  transition: 0.25s ease;
}

input:checked + .slider {
  background-color: #0545ef;
}

input:checked + .slider:before {
  transform: translateX(1.25rem);
}

.remember-me span {
  font-size: 0.875rem;
  font-weight: 500;
  color: #595c5e;
}

.actions {
  padding-top: 1rem;
}

/* Smooth, manually-controlled primary button animation:
   - default: pill
   - hover: via .is-hover (set by mouseenter/mouseleave)
   - loading: morphs into rounded-rectangle smoothly
*/
.primary-button {
  width: 100%;
  background-color: #0545ef;
  color: #f2f1ff;
  padding: 0.9rem 1rem;
  border-radius: 9999px; /* pill */
  font-weight: 700;
  font-size: 1rem;
  border: none;
  cursor: pointer;

  /* GPU-friendly transitions */
  transform: translateZ(0);
  will-change: transform, box-shadow, border-radius;
  transition:
    background-color 180ms ease,
    transform 180ms ease,
    box-shadow 220ms ease,
    border-radius 420ms cubic-bezier(0.2, 0.9, 0.2, 1),
    filter 180ms ease;

  box-shadow: 0 12px 24px -8px rgba(5, 69, 239, 0.3);
}

.primary-button.is-hover {
  background-color: #003bd4;
  transform: translateY(-1px);
  box-shadow: 0 16px 28px -10px rgba(5, 69, 239, 0.35);
}

.primary-button:active {
  transform: translateY(0px) scale(0.99);
}

.primary-button:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px rgba(5, 69, 239, 0.25),
    0 16px 28px -10px rgba(5, 69, 239, 0.35);
}

/* "Logging in" state: morph pill -> rounded-rectangle smoothly */
.primary-button.is-loading,
.primary-button:disabled {
  cursor: not-allowed;
  background-color: #595c5e;
  border-radius: 1rem; /* less pill, more long rounded corners */
  box-shadow: 0 12px 18px -10px rgba(44, 47, 49, 0.25);
  transform: none;
  filter: saturate(0.9);
}

/* Safety: if hover class sticks during loading, keep loading visuals */
.primary-button.is-loading.is-hover {
  background-color: #595c5e;
  transform: none;
  box-shadow: 0 12px 18px -10px rgba(44, 47, 49, 0.25);
}

@media (prefers-reduced-motion: reduce) {
  .primary-button {
    transition: background-color 180ms ease, box-shadow 220ms ease, border-radius 250ms ease;
  }
  .primary-button.is-hover {
    transform: none;
  }
}

.sso-divider {
  margin-top: 2.5rem;
  position: relative;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sso-divider .line {
  width: 100%;
  border-top: 1px solid rgba(171, 173, 175, 0.15);
}

.sso-divider span {
  background-color: #f5f7f9;
  padding: 0 1rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #595c5e;
  font-weight: 700;
}

.sso-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.sso-buttons button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #ffffff;
  border: 1px solid rgba(171, 173, 175, 0.15);
  border-radius: 9999px;
  transition: border-radius 0.3s ease-in-out, background-color 0.3s ease-in-out;
  cursor: pointer;
}

.sso-buttons button:hover {
  background-color: #eef1f3;
  border-radius: 1rem;
}

.sso-buttons img {
  width: 1.25rem;
  height: 1.25rem;
}

.sso-buttons span {
  font-size: 0.875rem;
  font-weight: 600;
  color: #595c5e;
}

.signup-link {
  margin-top: 3rem;
  text-align: center;
}

.signup-link p {
  color: #595c5e;
  font-size: 0.875rem;
}

.signup-link a {
  color: #0545ef;
  font-weight: 700;
  text-decoration: none;
  margin-left: 0.25rem;
}
.signup-link a:hover {
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