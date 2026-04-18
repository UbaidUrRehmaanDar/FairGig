import { defineNuxtConfig } from "nuxt/config"

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY

export default defineNuxtConfig({
  css: ['~/assets/css/app.css'],
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
      apiBase: "http://localhost:8000",
      anomalyBase: "http://localhost:8001",
    },
  },
})
