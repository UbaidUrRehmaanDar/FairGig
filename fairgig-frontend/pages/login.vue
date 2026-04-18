<template>
  <section>
    <h2>Login</h2>
    <form class="form" @submit.prevent>
      <input type="email" placeholder="Email" required />
      <input type="password" placeholder="Password" required />
      <button type="button">Sign In</button>
    </form>
    <p class="hint">Auth wiring will be connected in the implementation phase.</p>
  </section>
</template>

<style scoped>
.form {
  display: grid;
  gap: 0.75rem;
  max-width: 340px;
}

.hint {
  color: #555;
}
</style>
