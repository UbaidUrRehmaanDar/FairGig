import { defineStore } from 'pinia'
import { ref } from 'vue'

export type FairGigRole = 'worker' | 'verifier' | 'advocate'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const role = ref<FairGigRole>('worker')

  // Load from local storage for demo if available
  if (typeof window !== 'undefined') {
    const saved = window.localStorage.getItem('fg_demo_persona') as FairGigRole
    if (saved && ['worker', 'verifier', 'advocate'].includes(saved)) {
      role.value = saved
    }
  }

  const signUp = async () => ({ status: 'skeleton' })
  const signIn = async () => ({ status: 'skeleton' })
  const signOut = async () => ({ status: 'skeleton' })

  return {
    user,
    role,
    signUp,
    signIn,
    signOut
  }
})
