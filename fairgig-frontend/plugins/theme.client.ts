export default defineNuxtPlugin(() => {
  if (process.server) return

  try {
    const saved = window.localStorage.getItem('fg_theme')
    const shouldUseDark = saved === 'dark'

    document.documentElement.classList.toggle('dark', shouldUseDark)
  } catch {
    // Ignore storage errors (private mode / disabled storage)
  }
})
