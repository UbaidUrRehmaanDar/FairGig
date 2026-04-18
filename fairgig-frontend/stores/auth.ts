import type { User } from '@supabase/supabase-js'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type FairGigRole = 'worker' | 'verifier' | 'advocate'

const normalizeRole = (value: unknown): FairGigRole => {
  const normalized = String(value ?? '').toLowerCase().trim()
  if (normalized === 'advocate') return 'advocate'
  if (normalized === 'verifier') return 'verifier'
  return 'worker'
}

const resolveRoleFromUser = (user: User | null | undefined): FairGigRole => {
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

export const useAuthStore = defineStore('auth', () => {
  const supabase = useSupabaseClient()

  const user = ref<User | null>(null)
  const role = ref<FairGigRole>('worker')
  const initialized = ref(false)

  const isAuthenticated = computed(() => Boolean(user.value))

  const refreshSession = async () => {
    const { data } = await supabase.auth.getSession()
    user.value = data.session?.user || null
    role.value = readDemoPersona() || resolveRoleFromUser(user.value)
    initialized.value = true
    return { user: user.value, role: role.value }
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
    const result = await supabase.auth.signOut()
    user.value = null
    role.value = 'worker'
    initialized.value = true
    return result
  }

  return {
    user,
    role,
    initialized,
    isAuthenticated,
    refreshSession,
    signUp,
    signIn,
    signOut
  }
})
