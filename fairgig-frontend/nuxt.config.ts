import { defineNuxtConfig } from "nuxt/config"

export default defineNuxtConfig({
  modules: ["@pinia/nuxt", "@nuxtjs/supabase"],
  supabase: {
    redirectOptions: {
      login: "/login",
      callback: "/confirm",
      exclude: ["/", "/grievances", "/register"],
    },
  },
  runtimeConfig: {
    public: {
      apiBase: "http://localhost:8000",
      anomalyBase: "http://localhost:8001",
    },
  },
})
