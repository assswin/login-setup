const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    if (response.status === 405) {
      throw new Error(
        'Backend API is not available on static GitHub Pages (405). GitHub Pages only hosts static files and cannot run Python. Run locally at http://127.0.0.1:8000 or deploy to Vercel.'
      )
    }
    const detail = data.detail
    const message =
      typeof detail === 'string'
        ? detail
        : typeof data.message === 'string'
          ? data.message
          : `Request failed: ${response.status}`

    throw new Error(message)
  }

  return data as T
}
