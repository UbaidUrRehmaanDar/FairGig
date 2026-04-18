<template>
  <div class="app-shell">
    <header class="topbar">
      <h1>FairGig</h1>
      <nav>
        <NuxtLink to="/">Home</NuxtLink>
        <NuxtLink to="/dashboard/worker">Worker</NuxtLink>
        <NuxtLink to="/dashboard/verifier">Verifier</NuxtLink>
        <NuxtLink to="/dashboard/advocate">Advocate</NuxtLink>
        <NuxtLink to="/grievances">Grievances</NuxtLink>
      </nav>
    </header>
    <main>
      <slot />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #ddd;
}

nav {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

main {
  max-width: 960px;
  margin: 0 auto;
  padding: 1rem;
}
</style>
