import { ApiError, getApiBaseUrl } from './api'

export interface AuthenticatedUser {
  id: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AccessTokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

function isAccessTokenResponse(value: unknown): value is AccessTokenResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'access_token' in value &&
    typeof value.access_token === 'string' &&
    'token_type' in value &&
    value.token_type === 'bearer' &&
    'expires_in' in value &&
    typeof value.expires_in === 'number' &&
    value.expires_in > 0
  )
}

function isAuthenticatedUser(value: unknown): value is AuthenticatedUser {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    typeof value.id === 'string' &&
    'email' in value &&
    typeof value.email === 'string' &&
    'is_active' in value &&
    typeof value.is_active === 'boolean' &&
    'created_at' in value &&
    typeof value.created_at === 'string' &&
    'updated_at' in value &&
    typeof value.updated_at === 'string'
  )
}

async function readTokenResponse(
  response: Response,
): Promise<AccessTokenResponse> {
  if (!response.ok) {
    throw new ApiError(response.status, 'Authentication request failed')
  }

  const payload: unknown = await response.json()
  if (!isAccessTokenResponse(payload)) {
    throw new Error('Authentication response does not match the contract')
  }
  return payload
}

export async function login(
  email: string,
  password: string,
): Promise<AccessTokenResponse> {
  const body = new URLSearchParams({
    username: email,
    password,
  })
  const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/token`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  })
  return readTokenResponse(response)
}

export async function refreshAccessToken(): Promise<AccessTokenResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  })
  return readTokenResponse(response)
}

export async function logoutSession(): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/logout`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  })
  if (!response.ok) {
    throw new ApiError(response.status, 'Logout request failed')
  }
}

export async function getCurrentUser(
  accessToken: string,
): Promise<AuthenticatedUser> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/users/me`, {
    credentials: 'omit',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
  })
  if (!response.ok) {
    throw new ApiError(response.status, 'Current user request failed')
  }

  const payload: unknown = await response.json()
  if (!isAuthenticatedUser(payload)) {
    throw new Error('Current user response does not match the contract')
  }
  return payload
}
