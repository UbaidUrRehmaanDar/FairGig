export const useApi = () => {
  const apiBase = "http://localhost:8000"

  const authFetch = async <T = any>(path: string, options: RequestInit = {}) => {
    const response = await fetch(`${apiBase}${path}`, options)
    return (await response.json()) as T
  }

  return { authFetch }
}
