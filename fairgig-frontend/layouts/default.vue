<template>
  <div class="app-shell">
    <header class="topbar no-print">
      <div class="topbar-inner">
        <NuxtLink to="/" class="brand">FairGig</NuxtLink>

        <nav class="nav-links">
          <NuxtLink to="/dashboard/worker">Dashboard</NuxtLink>
          <NuxtLink to="/shifts">Shifts</NuxtLink>
          <NuxtLink to="/grievances">Grievances</NuxtLink>
          <NuxtLink to="/certificate">Certificate</NuxtLink>
          <NuxtLink to="/settings">Settings</NuxtLink>
        </nav>
      </div>
    </header>

    <main class="page-slot">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--fg-bg);
  backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--fg-border);
}

.topbar-inner {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0.85rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.brand {
  text-decoration: none;
  color: var(--fg-primary);
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.nav-links {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}
.nav-links a {
  text-decoration: none;
  color: var(--fg-muted);
  font-size: 0.86rem;
  font-weight: 700;
  padding: 0.45rem 0.7rem;
  border-radius: 9999px;
  transition: 0.2s;
}
.nav-links a:hover,
.nav-links a.router-link-active {
  background: var(--fg-surface-muted);
  color: var(--fg-text);
}

.page-slot {
  min-height: calc(100vh - 64px);
}
</style>