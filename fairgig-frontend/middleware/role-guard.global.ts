const dashboardByRole = {
  worker: '/dashboard/worker',
  verifier: '/dashboard/verifier',
  advocate: '/dashboard/advocate',
} as const

const isProtectedRoute = (path: string) => {
  return (
    path.startsWith('/dashboard') ||
    path.startsWith('/shifts') ||
    path.startsWith('/certificate') ||
    path.startsWith('/grievances')
  )
}

export default defineNuxtRouteMiddleware(async (to) => {
  if (!isProtectedRoute(to.path)) return

  const supabase = useSupabaseClient()
  const authStore = useAuthStore()

  try {
    if (!authStore.initialized) {
      await authStore.refreshSession()
    }
  } catch {
    return navigateTo('/login')
  }

  const { data } = await supabase.auth.getSession()
  const sessionUser = data.session?.user || null
  if (!sessionUser) {
    return navigateTo('/login')
  }

  const currentRole = authStore.role || 'worker'

  if (to.path.startsWith('/dashboard/worker') || to.path.startsWith('/shifts') || to.path.startsWith('/certificate')) {
    if (currentRole !== 'worker') return navigateTo(dashboardByRole[currentRole])
    return
  }

  if (to.path.startsWith('/dashboard/verifier')) {
    if (currentRole !== 'verifier') return navigateTo(dashboardByRole[currentRole])
    return
  }

  if (to.path.startsWith('/dashboard/advocate')) {
    if (currentRole !== 'advocate') return navigateTo(dashboardByRole[currentRole])
    return
  }

  if (to.path.startsWith('/grievances/new') && currentRole !== 'worker') {
    return navigateTo(dashboardByRole[currentRole])
  }

  if (to.path.startsWith('/grievances') && currentRole === 'verifier') {
    return navigateTo(dashboardByRole[currentRole])
  }
})