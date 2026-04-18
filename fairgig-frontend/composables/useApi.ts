export const useApi = () => {
  const config = useRuntimeConfig()
  const supabase = useSupabaseClient()
  const apiBase = String(config.public.apiBase || "http://127.0.0.1:8000").replace(/\/$/, "")

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
    let response: Response
    try {
      response = await fetch(`${apiBase}${normalizedPath}`, {
        ...options,
        body,
        headers,
      })
    } catch {
      throw new Error(`Cannot reach API at ${apiBase}. Ensure backend is running.`)
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
