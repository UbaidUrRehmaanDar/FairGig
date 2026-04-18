import { defineNuxtConfig } from "nuxt/config"
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const appRoot = fileURLToPath(new URL('.', import.meta.url))

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY

export default defineNuxtConfig({
  css: ['~/assets/css/app.css'],
  compatibilityDate: '2026-04-18',
  vite: {
    resolve: {
      alias: {
        '#app-manifest': resolve(appRoot, '.nuxt/manifest/meta/dev.json')
      }
    }
  },
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
      apiBase: "http://127.0.0.1:8000",
      anomalyBase: "http://127.0.0.1:8001",
    },
  },
})
