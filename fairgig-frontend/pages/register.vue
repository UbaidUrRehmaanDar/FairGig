<template>
  <section>
    <h2>Register</h2>
    <form class="form" @submit.prevent>
      <input placeholder="Full Name" required />
      <input type="email" placeholder="Email" required />
      <input type="password" placeholder="Password" required />
      <select>
        <option value="worker">Worker</option>
        <option value="verifier">Verifier</option>
        <option value="advocate">Advocate</option>
      </select>
      <input placeholder="City Zone" required />
      <input placeholder="Platform Category" required />
      <button type="button">Create Account</button>
    </form>
    <p class="hint">Signup + profile setup will be wired in the implementation phase.</p>
  </section>
</template>

<style scoped>
.form {
  display: grid;
  gap: 0.75rem;
  max-width: 420px;
}

.hint {
  color: #555;
}
</style>
