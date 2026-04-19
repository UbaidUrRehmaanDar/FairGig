import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type FairGigRole = 'worker' | 'verifier' | 'advocate'

const normalizeRole = (value: unknown): FairGigRole => {
  const normalized = String(value ?? '').toLowerCase().trim()
  if (normalized === 'advocate') return 'advocate'
  if (normalized === 'verifier') return 'verifier'
  return 'worker'
}

const resolveRoleFromUser = (user: any): FairGigRole => {
  const candidate =
    (typeof user?.user_metadata?.role === 'string' && user.user_metadata.role) ||
    (typeof user?.app_metadata?.role === 'string' && user.app_metadata.role) ||
    'worker'

  return normalizeRole(candidate)
}

const readDemoPersona = (): FairGigRole | null => {
  if (typeof window === 'undefined') return null
  try {
    const saved = window.localStorage.getItem('fg_demo_persona')
    if (!saved) return null
    return normalizeRole(saved)
  } catch {
    return null
  }
}

const clearPersistedAuthState = () => {
  if (typeof window === 'undefined') return

  const shouldRemove = (key: string) => {
    if (key === 'supabase.auth.token') return true
    if (!key.startsWith('sb-')) return false
    return (
      key.includes('auth-token') ||
      key.includes('refresh-token') ||
      key.includes('code-verifier')
    )
  }

  const clearStorage = (storage: Storage) => {
    for (let i = storage.length - 1; i >= 0; i -= 1) {
      const key = storage.key(i)
      if (!key) continue
      if (shouldRemove(key)) {
        storage.removeItem(key)
      }
    }
  }

  try {
    clearStorage(window.localStorage)
    clearStorage(window.sessionStorage)
  } catch {
    // ignore storage access errors in restricted browser modes
  }
}

export const useAuthStore = defineStore('auth', () => {
  const supabase = useSupabaseClient()

  const role = ref<FairGigRole>('worker')
  const initialized = ref(false)

  const isAuthenticated = computed(() => Boolean(initialized.value))

  const refreshSession = async () => {
    const { data } = await supabase.auth.getSession()
    const sessionUser = data.session?.user || null
    role.value = readDemoPersona() || resolveRoleFromUser(sessionUser)
    initialized.value = true
    return { role: role.value }
  }

  // Load demo persona for UI routing if available (does not affect backend permissions).
  const demoPersona = readDemoPersona()
  if (demoPersona) {
    role.value = demoPersona
  }

  const signUp = async (payload: {
    email: string
    password: string
    options?: any
  }) => {
    const result = await supabase.auth.signUp(payload)
    await refreshSession()
    return result
  }

  const signIn = async (payload: { email: string; password: string }) => {
    const result = await supabase.auth.signInWithPassword(payload)
    await refreshSession()
    return result
  }

  const signOut = async () => {
    let lastError: unknown = null

    try {
      const result = await supabase.auth.signOut({ scope: 'global' })
      if (result.error) lastError = result.error
    } catch (error) {
      lastError = error
    }

    try {
      await supabase.auth.signOut({ scope: 'local' })
    } catch {
      // ignore and continue with local cleanup
    }

    clearPersistedAuthState()

    role.value = readDemoPersona() || 'worker'
    initialized.value = true
    return { error: lastError }
  }

  return {
    role,
    initialized,
    isAuthenticated,
    refreshSession,
    signUp,
    signIn,
    signOut
  }
})
