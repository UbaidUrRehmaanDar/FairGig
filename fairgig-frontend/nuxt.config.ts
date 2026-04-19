import { defineNuxtConfig } from "nuxt/config"

const supabaseUrl = (
  process.env.SUPABASE_URL ||
  process.env.NUXT_PUBLIC_SUPABASE_URL ||
  ''
).trim().replace(/\/$/, '')
const supabaseKey = (
  process.env.SUPABASE_KEY ||
  process.env.SUPABASE_ANON_KEY ||
  process.env.NUXT_PUBLIC_SUPABASE_KEY ||
  process.env.NUXT_PUBLIC_SUPABASE_ANON_KEY ||
  ''
).trim()
const coreApiUrl = (process.env.NUXT_PUBLIC_CORE_API_URL || process.env.NUXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000').replace(/\/$/, '')
const anomalyApiUrl = (process.env.NUXT_PUBLIC_ANOMALY_API_URL || process.env.NUXT_PUBLIC_ANOMALY_BASE || 'http://127.0.0.1:8001').replace(/\/$/, '')
const grievanceApiUrl = (process.env.NUXT_PUBLIC_GRIEVANCE_API_URL || process.env.NUXT_PUBLIC_GRIEVANCE_BASE || 'http://127.0.0.1:3002').replace(/\/$/, '')

export default defineNuxtConfig({
  css: ['~/assets/css/app.css'],
  compatibilityDate: '2026-04-18',
  app: {
    head: {
      link: [
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600;700;800&display=swap'
        },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200'
        }
      ]
    }
  },
  modules: ["@pinia/nuxt", "@nuxtjs/supabase"],
  supabase: {
    url: supabaseUrl,
    key: supabaseKey,
    redirectOptions: {
      login: "/login",
      callback: "/confirm",
      exclude: ["/", "/grievances", "/register"],
    },
  },
  nitro: {
    compatibilityDate: '2026-04-18'
  },
  runtimeConfig: {
    public: {
      apiBase: coreApiUrl,
      anomalyBase: anomalyApiUrl,
      grievanceBase: grievanceApiUrl,
    },
  },
})
