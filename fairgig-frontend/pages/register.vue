<template>
  <div class="register-container">
    <!-- Left Column: Editorial Branded Visual -->
    <section class="left-section">
      <div class="background-image">
        <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuBhWrqvAtkl6Lp7L7P4VaWgJNexlQSaq9todvpKQp_QV61ItYDJ2fOrPZvhOqIuQsOygnBe2yBgFwk18c9SzBjTKHBTyHDM_5MHPih8i-VMbdC_JBIHHQfq2L0lGVugnmw4ONKtO6gy9-vDm0CNuVSOIXjiV6RX-_dm9Uqcv1SXQ8YgBdUiwYIkEvKw9MfzEThBY7byhCqQbYu3abBagf9UEucpJTSIU5eEaaV4CVMCI5P6_ZR7hiUkMid6NJA8rx_Yy1OFVidOhoc" alt="Candid shot of a diverse group of modern gig workers collaborating in a bright, contemporary co-working space" />
        <div class="gradient-overlay"></div>
      </div>
      <div class="content">
        <div class="logo">FairGig</div>
        <h1>Join the <span class="highlight">FairGig</span> community today.</h1>
        <p>Empowering independent workers with a community built on transparency, unity, and shared success.</p>
      </div>
      <div class="partners">
        <div class="avatars">
          <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuBhWrqvAtkl6Lp7L7P4VaWgJNexlQSaq9todvpKQp_QV61ItYDJ2fOrPZvhOqIuQsOygnBe2yBgFwk18c9SzBjTKHBTyHDM_5MHPih8i-VMbdC_JBIHHQfq2L0lGVugnmw4ONKtO6gy9-vDm0CNuVSOIXjiV6RX-_dm9Uqcv1SXQ8YgBdUiwYIkEvKw9MfzEThBY7byhCqQbYu3abBagf9UEucpJTSIU5eEaaV4CVMCI5P6_ZR7hiUkMid6NJA8rx_Yy1OFVidOhoc" alt="Candid shot of a diverse group of modern gig workers collaborating in a bright, contemporary co-working space" />
          <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuBhWrqvAtkl6Lp7L7P4VaWgJNexlQSaq9todvpKQp_QV61ItYDJ2fOrPZvhOqIuQsOygnBe2yBgFwk18c9SzBjTKHBTyHDM_5MHPih8i-VMbdC_JBIHHQfq2L0lGVugnmw4ONKtO6gy9-vDm0CNuVSOIXjiV6RX-_dm9Uqcv1SXQ8YgBdUiwYIkEvKw9MfzEThBY7byhCqQbYu3abBagf9UEucpJTSIU5eEaaV4CVMCI5P6_ZR7hiUkMid6NJA8rx_Yy1OFVidOhoc" alt="Candid shot of a diverse group of modern gig workers collaborating in a bright, contemporary co-working space" />
          <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuBhWrqvAtkl6Lp7L7P4VaWgJNexlQSaq9todvpKQp_QV61ItYDJ2fOrPZvhOqIuQsOygnBe2yBgFwk18c9SzBjTKHBTyHDM_5MHPih8i-VMbdC_JBIHHQfq2L0lGVugnmw4ONKtO6gy9-vDm0CNuVSOIXjiV6RX-_dm9Uqcv1SXQ8YgBdUiwYIkEvKw9MfzEThBY7byhCqQbYu3abBagf9UEucpJTSIU5eEaaV4CVMCI5P6_ZR7hiUkMid6NJA8rx_Yy1OFVidOhoc" alt="Candid shot of a diverse group of modern gig workers collaborating in a bright, contemporary co-working space" />
        </div>
        <p>Joined by 10k+ institutional partners</p>
      </div>
    </section>

    <!-- Right Column: Registration Form -->
    <section class="right-section">
      <div class="mobile-header">
        <span class="logo">FairGig</span>
      </div>
      <div class="form-wrapper">
        <div class="form-header">
          <h2>Create Account</h2>
          <p>Begin your journey towards ethereal financial management.</p>
        </div>
        <form class="register-form" @submit.prevent>
          <div class="input-group">
            <label for="full_name">Full Name</label>
            <input id="full_name" type="text" />
          </div>
          <div class="input-group">
            <label for="email">Email Address</label>
            <input id="email" type="email" />
          </div>
          <div class="password-group">
            <div class="input-group">
              <label for="password">Password</label>
              <input id="password" type="password" />
            </div>
            <div class="input-group">
              <label for="confirm_password">Confirm Password</label>
              <input id="confirm_password" type="password" />
            </div>
          </div>
          <div class="terms-group">
            <input id="terms" type="checkbox" />
            <label for="terms">
              I agree to the <a href="#">Terms & Conditions</a> and acknowledge the Privacy Policy.
            </label>
          </div>
          <button type="submit">Create Account</button>
        </form>
        <div class="login-link">
          <p>
            Already have an account?
            <a href="/login">Log in instead</a>
          </p>
        </div>
        <div class="footer-links">
          <a href="#">Institutional</a>
          <a href="#">Security</a>
          <a href="#">Help</a>
        </div>
      </div>
    </section>
  </div>
</template>

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
  position: relative;
  width: 50%;
  flex-direction: column;
  justify-content: space-between;
  padding: 4rem;
  overflow: hidden;
}

.background-image {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.background-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom right, rgba(5, 69, 239, 0.4), rgba(245, 247, 249, 0.1), rgba(44, 47, 49, 0.6));
  mix-blend-mode: multiply;
}

.content, .partners {
  position: relative;
  z-index: 10;
}

.logo {
  font-size: 1.875rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: #f2f1ff;
  margin-bottom: 6rem;
}

h1 {
  font-family: 'Raleway', sans-serif;
  font-size: 3.75rem;
  font-weight: 800;
  color: #f2f1ff;
  line-height: 1.1;
  letter-spacing: -0.025em;
  max-width: 28rem;
}

.highlight {
  color: #859aff;
}

.left-section > .content > p {
  margin-top: 2rem;
  font-size: 1.25rem;
  color: rgba(242, 241, 255, 0.8);
  font-weight: 500;
  max-width: 28rem;
  line-height: 1.6;
}

.partners {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.avatars {
  display: flex;
  margin-left: -0.75rem;
}

.avatars img {
  width: 3rem;
  height: 3rem;
  border-radius: 9999px;
  border: 2px solid #f2f1ff;
  object-fit: cover;
}

.partners p {
  font-size: 0.875rem;
  color: #f2f1ff;
  font-weight: 500;
}

/* Right Section */
.right-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 3rem 2rem;
}

.mobile-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 3rem;
}

.mobile-header .logo {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: #0545ef;
}

.form-wrapper {
  max-width: 28rem;
  width: 100%;
  margin: 0 auto;
}

.form-header {
  margin-bottom: 2.5rem;
}

.form-header h2 {
  font-family: 'Raleway', sans-serif;
  font-size: 1.875rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  margin-bottom: 0.5rem;
}

.form-header p {
  color: #595c5e;
}

.register-form {
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
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #595c5e;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 0.25rem;
}

.input-group input {
  width: 100%;
  padding: 1rem;
  background-color: #eef1f3;
  border: none;
  border-radius: 1rem;
  color: #2c2f31;
  transition: all 0.2s;
}

.input-group input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(5, 69, 239, 0.2);
  background-color: #ffffff;
}

.password-group {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.terms-group {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.5rem 0;
}

.terms-group input {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 0.25rem;
  border-color: #d9dde0;
  background-color: #eef1f3;
  color: #0545ef;
}

.terms-group input:focus {
  ring: #0545ef;
  ring-offset-color: #0545ef;
}

.terms-group label {
  font-size: 0.875rem;
  color: #595c5e;
  line-height: 1.3;
}

.terms-group a {
  color: #0545ef;
  font-weight: 600;
  text-decoration: none;
}
.terms-group a:hover {
  text-decoration: underline;
}

.register-form button {
  width: 100%;
  padding: 0.9rem 1rem;
  background-color: #0545ef;
  color: #f2f1ff;
  font-weight: 700;
  border-radius: 9999px;
  font-size: 1rem;
  box-shadow: 0 24px 24px -4px rgba(5, 69, 239, 0.15);
  transform: translateZ(0);
  will-change: transform, border-radius;
  transition: background-color 0.2s ease, border-radius 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
  border: none;
  cursor: pointer;
}

.register-form button:hover {
  background-color: #003bd4;
  border-radius: 1rem;
  box-shadow: 0 32px 28px -12px rgba(5, 69, 239, 0.22);
  animation: primary-button-boom 220ms cubic-bezier(0.2, 0.9, 0.2, 1) both;
}

.register-form button:active {
  animation: none;
  transform: scale(0.985);
}

.register-form button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(5, 69, 239, 0.25), 0 24px 24px -4px rgba(5, 69, 239, 0.15);
}

@keyframes primary-button-boom {
  0% {
    transform: scale(1);
  }
  60% {
    transform: scale(1.07);
  }
  100% {
    transform: scale(1.04);
  }
}

@media (prefers-reduced-motion: reduce) {
  .register-form button {
    transition: background-color 0.2s ease, border-radius 0.25s ease, box-shadow 0.25s ease;
  }
  .register-form button:hover {
    animation: none;
  }
}

.login-link {
  margin-top: 2.5rem;
  text-align: center;
}

.login-link p {
  color: #595c5e;
  font-weight: 500;
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

.footer-links {
  margin-top: 4rem;
  display: flex;
  justify-content: center;
  gap: 2rem;
  opacity: 0.4;
}

.footer-links a {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #2c2f31;
  text-decoration: none;
  transition: opacity 0.2s;
}

.footer-links a:hover {
  opacity: 1;
}

@media (min-width: 1024px) {
  .left-section {
    display: flex;
  }
  .right-section {
    width: 50%;
  }
  .mobile-header {
    display: none;
  }
  .password-group {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

