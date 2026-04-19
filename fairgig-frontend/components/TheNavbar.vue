<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useAuthStore } from '~/stores/auth'
import { useLanguage } from '~/composables/useLanguage'

const authStore = useAuthStore()
const { role } = storeToRefs(authStore)
const { t, isUrdu } = useLanguage()
</script>

<template>
  <nav class="iphone-nav">
    <!-- Worker Links -->
    <template v-if="role === 'worker'">
      <NuxtLink to="/dashboard/worker" class="nav-item">
        <span class="material-symbols-outlined">dashboard</span>
        <span class="text">{{ t('nav.home') }}</span>
      </NuxtLink>
      <NuxtLink to="/shifts" class="nav-item">
        <span class="material-symbols-outlined">schedule</span>
        <span class="text">{{ t('nav.shifts') }}</span>
      </NuxtLink>
      <NuxtLink to="/grievances" class="nav-item">
        <span class="material-symbols-outlined">campaign</span>
        <span class="text">{{ t('nav.grievances') }}</span>
      </NuxtLink>
      <NuxtLink to="/certificate" class="nav-item">
        <span class="material-symbols-outlined">description</span>
        <span class="text">{{ t('nav.docs') }}</span>
      </NuxtLink>
    </template>

    <!-- Advocate Links -->
    <template v-else-if="role === 'advocate'">
      <NuxtLink to="/dashboard/advocate" class="nav-item">
        <span class="material-symbols-outlined">monitoring</span>
        <span class="text">{{ t('nav.analytics') }}</span>
      </NuxtLink>
      <NuxtLink to="/grievances" class="nav-item">
        <span class="material-symbols-outlined">campaign</span>
        <span class="text">{{ t('nav.grievances') }}</span>
      </NuxtLink>
      <NuxtLink to="/settings" class="nav-item">
        <span class="material-symbols-outlined">settings</span>
        <span class="text">Settings</span>
      </NuxtLink>
    </template>

    <!-- Verifier Links -->
    <template v-else-if="role === 'verifier'">
      <NuxtLink to="/dashboard/verifier" class="nav-item">
        <span class="material-symbols-outlined">verified</span>
        <span class="text">{{ t('nav.verify') }}</span>
      </NuxtLink>
      <NuxtLink to="/settings" class="nav-item">
        <span class="material-symbols-outlined">settings</span>
        <span class="text">{{ t('nav.settings') }}</span>
      </NuxtLink>
    </template>
  </nav>
</template>

<style scoped>
.iphone-nav {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 2rem);
  max-width: 24rem;
  display: flex;
  justify-content: space-around;
  background-color: color-mix(in srgb, var(--fg-surface) 80%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 2rem;
  padding: 0.75rem 0.5rem;
  box-shadow: var(--fg-shadow);
  z-index: 1000;
  border: 1px solid var(--fg-border);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: var(--fg-muted);
  transition: all 0.2s ease;
  padding: 0.25rem 0.75rem;
  border-radius: 1.25rem;
  flex: 1;
}

.nav-item .material-symbols-outlined {
  font-size: 1.6rem;
  margin-bottom: 0.125rem;
}

.nav-item .text {
  font-size: 0.7rem;
  font-weight: 700;
  word-wrap: break-word;
  max-width: 4rem;
  font-family: 'Raleway', sans-serif;
}

.nav-item.router-link-active {
  color: var(--fg-primary);
  background-color: color-mix(in srgb, var(--fg-primary) 10%, transparent);
}

/* ===== Mobile support patch (keep same component) ===== */
@media (max-width: 1023px) {
  .iphone-nav {
    bottom: max(1rem, env(safe-area-inset-bottom));
    width: calc(100% - 1.5rem);
    max-width: 100%;
    border-radius: 1.5rem;
    padding: 0.5rem;
    gap: 0.25rem;
  }

  .nav-item {
    min-height: 3.2rem;
    padding: 0.4rem 0.2rem;
    border-radius: 1.1rem;
    justify-content: center;
    gap: 0.12rem;
  }

  .nav-item .material-symbols-outlined {
    font-size: 1.4rem;
  }
}

/* extra small phones */
@media (max-width: 380px) {
  .iphone-nav {
    width: calc(100% - 1rem);
    padding: 0.4rem;
  }

  .nav-item .text {
    font-size: 0.65rem;
  }
}

/* hide navbar on desktop */
@media (min-width: 1024px) {
  .iphone-nav {
    display: none;
  }
}
</style>
