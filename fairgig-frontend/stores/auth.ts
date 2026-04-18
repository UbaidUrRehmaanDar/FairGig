import type { User } from '@supabase/supabase-js'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type FairGigRole = 'worker' | 'verifier' | 'advocate'

const resolveRole = (user: User | null | undefined): FairGigRole => {
  const candidate =
    (typeof user?.user_metadata?.role === 'string' && user.user_metadata.role) ||
    (typeof user?.app_metadata?.role === 'string' && user.app_metadata.role) ||
    'worker'

  const normalized = String(candidate).toLowerCase().trim()
  if (normalized === 'advocate') return 'advocate'
  if (normalized === 'verifier') return 'verifier'
  return 'worker'
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
    role.value = resolveRole(user.value)
    initialized.value = true
    return { user: user.value, role: role.value }
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
