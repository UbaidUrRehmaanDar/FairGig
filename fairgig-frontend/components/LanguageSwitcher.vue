<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useLanguage } from '~/composables/useLanguage'

const { language, setLanguage, loadTranslations, t } = useLanguage()
const isOpen = ref(false)

onMounted(async () => {
  await loadTranslations()
})

const switchLanguage = (lang: 'en' | 'ur') => {
  setLanguage(lang)
  isOpen.value = false
}
</script>

<template>
  <div class="language-switcher">
    <button
      class="lang-button"
      @click="isOpen = !isOpen"
      :title="t('common.language')"
      aria-label="Toggle language menu"
    >
      <span class="material-symbols-outlined">language</span>
      <span class="lang-text">{{ language.toUpperCase() }}</span>
    </button>

    <div v-if="isOpen" class="lang-dropdown">
      <button
        class="lang-option"
        :class="{ active: language === 'en' }"
        @click="switchLanguage('en')"
      >
        <span class="flag">🇺🇸</span>
        {{ t('common.english') }}
      </button>
      <button
        class="lang-option"
        :class="{ active: language === 'ur' }"
        @click="switchLanguage('ur')"
      >
        <span class="flag">🇵🇰</span>
        {{ t('common.urdu') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.language-switcher {
  position: relative;
  display: inline-block;
}

.lang-button {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem 0.75rem;
  background: var(--fg-surface-muted);
  border: 1px solid var(--fg-border);
  border-radius: 0.7rem;
  color: var(--fg-text);
  font-weight: 700;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.lang-button:hover {
  background: color-mix(in srgb, var(--fg-primary) 12%, var(--fg-surface));
  border-color: color-mix(in srgb, var(--fg-primary) 35%, var(--fg-border));
}

.lang-button .material-symbols-outlined {
  font-size: 1rem;
}

.lang-text {
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.lang-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.4rem;
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 0.7rem;
  box-shadow: var(--fg-shadow);
  z-index: 999;
  min-width: 140px;
  overflow: hidden;
}

[dir="rtl"] .lang-dropdown {
  right: auto;
  left: 0;
}

.lang-option {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.65rem 0.85rem;
  background: none;
  border: none;
  border-bottom: 1px solid var(--fg-border);
  color: var(--fg-text);
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

[dir="rtl"] .lang-option {
  text-align: right;
  flex-direction: row-reverse;
}

.lang-option:last-child {
  border-bottom: none;
}

.lang-option:hover {
  background: var(--fg-surface-muted);
}

.lang-option.active {
  background: color-mix(in srgb, var(--fg-primary) 15%, var(--fg-surface));
  color: var(--fg-primary);
  font-weight: 700;
}

.flag {
  font-size: 1.2rem;
}
</style>
