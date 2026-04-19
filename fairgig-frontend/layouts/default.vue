<template>
  <div class="app-shell" :class="{ 'no-topbar': !showTopbar }" :dir="direction">
    <header v-if="showTopbar" class="topbar no-print">
      <div class="topbar-inner">
        <div class="header-left">
          <button v-if="canGoBack" @click="goBack" class="back-button">
            <span class="material-symbols-outlined">arrow_back_ios</span>
          </button>
          <NuxtLink to="/" class="brand" v-if="!canGoBack">FairGig</NuxtLink>
          <span class="page-title" v-if="canGoBack">{{ pageTitle || 'FairGig' }}</span>
        </div>

        <nav class="nav-links desktop-only">
          <NuxtLink v-for="item in desktopNavLinks" :key="item.to" :to="item.to">{{ item.label }}</NuxtLink>
        </nav>

        <div class="topbar-actions desktop-only">
          <LanguageSwitcher />
        </div>

        <div class="mobile-actions mobile-only">
          <LanguageSwitcher />
          <NuxtLink to="/settings" class="settings-link">
            <span class="material-symbols-outlined">settings</span>
          </NuxtLink>
        </div>
      </div>
    </header>

    <main class="page-slot">
      <slot />
    </main>

    <TheNavbar v-if="showTopbar" class="mobile-only" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import TheNavbar from '~/components/TheNavbar.vue'
import LanguageSwitcher from '~/components/LanguageSwitcher.vue'
import { useLanguage } from '~/composables/useLanguage'
import { useAuthStore } from '~/stores/auth'

const route = useRoute()
const router = useRouter()
const { initLanguage, loadTranslations, direction, language } = useLanguage()
const authStore = useAuthStore()
const { role } = storeToRefs(authStore)

const showTopbar = computed(() => {
  const hideOn = ['/login', '/register', '/']
  return !hideOn.includes(route.path)
})

const canGoBack = computed(() => {
  const mainRoutes = ['/dashboard/worker', '/dashboard/advocate', '/dashboard/verifier', '/login', '/register', '/']
  return !mainRoutes.includes(route.path)
})

const desktopNavLinks = computed(() => {
  const currentRole = String(role.value || 'worker')

  if (currentRole === 'advocate') {
    return [
      { to: '/dashboard/advocate', label: 'Dashboard' },
      { to: '/grievances', label: 'Grievances' },
      { to: '/settings', label: 'Settings' },
    ]
  }

  if (currentRole === 'verifier') {
    return [
      { to: '/dashboard/verifier', label: 'Verify' },
      { to: '/settings', label: 'Settings' },
    ]
  }

  return [
    { to: '/dashboard/worker', label: 'Dashboard' },
    { to: '/shifts', label: 'Shifts' },
    { to: '/grievances', label: 'Grievances' },
    { to: '/certificate', label: 'Certificate' },
    { to: '/settings', label: 'Settings' },
  ]
})

const isMobile = ref(false)
const updateIsMobile = () => {
  if (process.client) {
    isMobile.value = window.innerWidth < 1024
  }
}

const pageTitle = computed(() => {
  const path = route.path
  if (path.includes('/certificate')) return 'Certificate'
  if (path.includes('/shifts/log')) return 'Log Shift'
  if (path.includes('/shifts')) return 'History'
  if (path.includes('/grievances/new')) return 'New Grievance'
  if (path.includes('/grievances')) return 'Grievances'
  if (path.includes('/settings')) return 'Settings'
  return ''
})

const goBack = () => {
  router.back()
}

onMounted(async () => {
  await loadTranslations()
  initLanguage()
  updateIsMobile()
  window.addEventListener('resize', updateIsMobile)
})
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
  padding-bottom: env(safe-area-inset-bottom);
}

.app-shell[dir="rtl"] {
  direction: rtl;
  text-align: right;
}

.app-shell[dir="ltr"] {
  direction: ltr;
  text-align: left;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: color-mix(in srgb, var(--fg-bg) 85%, transparent);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
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
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.back-button {
  background: transparent;
  border: none;
  color: var(--fg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  margin-left: -0.5rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.back-button:active {
  opacity: 0.6;
}

.back-button .material-symbols-outlined {
  font-size: 1.25rem;
  font-variation-settings: 'FILL' 1, 'wght' 700;
}

.page-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--fg-text);
  margin-left: 0.25rem;
}

.nav-links {
  display: flex;
  gap: 0.45rem;
}
.nav-links a {
  text-decoration: none;
  color: var(--fg-muted);
  font-size: 0.86rem;
  font-weight: 700;
  padding: 0.45rem 0.75rem;
  border-radius: 9999px;
  transition: 0.2s;
}
.nav-links a:hover,
.nav-links a.router-link-active {
  background: var(--fg-surface-muted);
  color: var(--fg-text);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mobile-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.settings-link {
  color: var(--fg-muted);
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  transition: 0.2s;
}

.settings-link:hover {
  background: var(--fg-surface-muted);
  color: var(--fg-text);
}

.page-slot {
  padding: var(--fg-page-padding);
  transition: padding 0.2s ease;
  min-height: calc(100vh - 64px);
}

.app-shell.no-topbar .page-slot {
  padding: 0;
  min-height: 100vh;
}

@media (max-width: 1024px) {
  .page-slot {
    padding: var(--fg-mobile-padding);
    padding-bottom: calc(var(--fg-mobile-nav-height) + 1rem);
  }
}
</style>