export function getApiBaseUrl(): string {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is not configured')
  }

  return apiBaseUrl.replace(/\/+$/, '')
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}
