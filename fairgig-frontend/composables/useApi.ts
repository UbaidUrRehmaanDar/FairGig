export const useApi = () => {
  const config = useRuntimeConfig()
  const supabase = useSupabaseClient()
  const apiBase = String(config.public.apiBase || "http://127.0.0.1:8000").replace(/\/$/, "")
  const grievanceBase = String(config.public.grievanceBase || apiBase).replace(/\/$/, "")

  const buildCandidateBases = (primary: string) => {
    const bases = [primary]

    if (primary.includes('127.0.0.1')) {
      bases.push(primary.replace('127.0.0.1', 'localhost'))
    } else if (primary.includes('localhost')) {
      bases.push(primary.replace('localhost', '127.0.0.1'))
    }

    return Array.from(new Set(bases))
  }

  type JsonLike = Record<string, any> | any[]
  type AuthFetchOptions = Omit<RequestInit, "body"> & {
    body?: RequestInit["body"] | JsonLike
  }

  const authFetch = async <T = any>(path: string, options: AuthFetchOptions = {}) => {
    const { data } = await supabase.auth.getSession()
    const token = data.session?.access_token

    const headers = new Headers(options.headers || {})
    if (!headers.has("Accept")) {
      headers.set("Accept", "application/json")
    }

    const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData
    const isStringBody = typeof options.body === "string"
    const shouldJsonEncodeBody = Boolean(options.body) && !isFormData && !isStringBody

    let body = options.body
    if (shouldJsonEncodeBody) {
      body = JSON.stringify(options.body)
    }

    if (body && !isFormData && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json")
    }

    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`)
    }

    const normalizedPath = path.startsWith("/") ? path : `/${path}`
    const serviceBase = normalizedPath.startsWith('/grievances') ? grievanceBase : apiBase
    const candidateBases = buildCandidateBases(serviceBase)

    let response: Response | null = null
    let lastNetworkError: unknown = null

    for (const base of candidateBases) {
      try {
        response = await fetch(`${base}${normalizedPath}`, {
          ...options,
          body,
          headers,
        })
        break
      } catch (error) {
        lastNetworkError = error
      }
    }

    if (!response) {
      const attempted = candidateBases.join(', ')
      const detail =
        lastNetworkError && typeof lastNetworkError === 'object' && 'message' in lastNetworkError
          ? String((lastNetworkError as any).message || '')
          : ''
      throw new Error(
        `Cannot reach API at ${attempted}. Ensure backend is running.${detail ? ` (${detail})` : ''}`
      )
    }

    const contentType = response.headers.get("content-type") || ""
    const isJson = contentType.includes("application/json")
    const payload = isJson ? await response.json().catch(() => null) : await response.text()

    if (!response.ok) {
      const detail =
        payload && typeof payload === "object" && "detail" in payload
          ? String((payload as any).detail)
          : ""
      throw new Error(detail || `Request failed (${response.status})`)
    }

    return payload as T
  }

  return { authFetch }
}
