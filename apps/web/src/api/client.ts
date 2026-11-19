import type { ProblemDetail, TokenResponse } from '@/api/types'

const API_BASE = '/api/v1'

let accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getAccessToken(): string | null {
  return accessToken
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fields: Record<string, string>

  constructor(status: number, code: string, message: string, fields: Record<string, string> = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fields = fields
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  let body: Partial<ProblemDetail> | null = null
  try {
    body = (await response.json()) as Partial<ProblemDetail>
  } catch {
    body = null
  }

  const fields: Record<string, string> = {}
  for (const item of body?.errors ?? []) {
    if (item?.field && item?.message) fields[item.field] = item.message
  }

  return new ApiError(
    response.status,
    body?.code ?? 'unknown',
    body?.detail ?? body?.title ?? `Request failed with status ${response.status}`,
    fields,
  )
}

let refreshInFlight: Promise<TokenResponse | null> | null = null

/** Single-flight refresh: concurrent callers share one rotation (ADR-0005). */
export function refreshSession(): Promise<TokenResponse | null> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          credentials: 'include',
        })
        if (!response.ok) {
          setAccessToken(null)
          return null
        }
        const session = (await response.json()) as TokenResponse
        setAccessToken(session.access_token)
        return session
      } catch {
        setAccessToken(null)
        return null
      } finally {
        refreshInFlight = null
      }
    })()
  }
  return refreshInFlight
}

const NO_RETRY_PATHS = new Set(['/auth/login', '/auth/register', '/auth/refresh', '/auth/logout'])

interface RequestOptions {
  retry?: boolean
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  })

  const mayRetry = options.retry !== false && !NO_RETRY_PATHS.has(path)
  if (response.status === 401 && mayRetry) {
    const session = await refreshSession()
    if (session) {
      return apiRequest<T>(path, init, { retry: false })
    }
  }

  if (!response.ok) {
    throw await toApiError(response)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
