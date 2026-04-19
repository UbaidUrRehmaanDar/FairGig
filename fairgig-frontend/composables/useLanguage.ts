import { ref, computed } from 'vue'

type Language = 'en' | 'ur'

const currentLanguage = ref<Language>('en')
const translations: Record<Language, Record<string, any>> = {
  en: {},
  ur: {},
}

export const useLanguage = () => {
  // Load translations
  const loadTranslations = async () => {
    if (!Object.keys(translations.en).length) {
      try {
        const enModule = await import('~/locales/en.json')
        const urModule = await import('~/locales/ur.json')
        translations.en = enModule.default
        translations.ur = urModule.default
      } catch (err) {
        console.error('Failed to load translations:', err)
      }
    }
  }

  // Initialize language from localStorage
  const initLanguage = () => {
    if (process.client) {
      const saved = localStorage.getItem('fairgig-language')
      if (saved === 'ur' || saved === 'en') {
        currentLanguage.value = saved
        document.documentElement.lang = saved
        document.documentElement.dir = saved === 'ur' ? 'rtl' : 'ltr'
      }
    }
  }

  // Set language
  const setLanguage = (lang: Language) => {
    currentLanguage.value = lang
    if (process.client) {
      localStorage.setItem('fairgig-language', lang)
      document.documentElement.lang = lang
      document.documentElement.dir = lang === 'ur' ? 'rtl' : 'ltr'
    }
  }

  // Get translation key
  const t = (path: string, defaultValue: string = path) => {
    const keys = path.split('.')
    let value: any = translations[currentLanguage.value]

    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key]
      } else {
        return defaultValue
      }
    }

    return typeof value === 'string' ? value : defaultValue
  }

  const language = computed(() => currentLanguage.value)
  const isUrdu = computed(() => currentLanguage.value === 'ur')
  const isEnglish = computed(() => currentLanguage.value === 'en')
  const direction = computed(() => isUrdu.value ? 'rtl' : 'ltr')

  return {
    loadTranslations,
    initLanguage,
    setLanguage,
    t,
    language,
    isUrdu,
    isEnglish,
    direction,
  }
}
