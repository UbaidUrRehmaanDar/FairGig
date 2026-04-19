import { useLanguage } from '~/composables/useLanguage'

export default defineNuxtPlugin(async () => {
  const { initLanguage, loadTranslations } = useLanguage()

  if (process.client) {
    await loadTranslations()
    initLanguage()
  }
})
