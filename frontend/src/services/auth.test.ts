import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  getCurrentUser,
  login,
  logoutSession,
  refreshAccessToken,
} from './auth'

const tokenPayload = {
  access_token: 'test-access-token',
  token_type: 'bearer',
  expires_in: 1800,
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('authentication service', () => {
  it('sends login as OAuth2 form data with browser credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(tokenPayload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await login('person@example.com', 'a-long-test-password')

    const [url, options] = fetchMock.mock.calls[0] as [
      string,
      RequestInit,
    ]
    expect(url).toBe('http://localhost:8000/api/v1/auth/token')
    expect(options.credentials).toBe('include')
    expect(options.method).toBe('POST')
    expect(options.body).toBeInstanceOf(URLSearchParams)
    expect((options.body as URLSearchParams).get('username')).toBe(
      'person@example.com',
    )
  })

  it('uses the HttpOnly cookie path for refresh and logout', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(tokenPayload), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await refreshAccessToken()
    await logoutSession()

    expect(fetchMock.mock.calls[0][0]).toBe(
      'http://localhost:8000/api/v1/auth/refresh',
    )
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      method: 'POST',
      credentials: 'include',
    })
    expect(fetchMock.mock.calls[1][0]).toBe(
      'http://localhost:8000/api/v1/auth/logout',
    )
    expect(fetchMock.mock.calls[1][1]).toMatchObject({
      method: 'POST',
      credentials: 'include',
    })
  })

  it('keeps the refresh cookie out of the current user request', async () => {
    const userPayload = {
      id: '68f05028-d75e-4bc1-8db2-520355f10331',
      email: 'person@example.com',
      is_active: true,
      created_at: '2026-07-30T12:00:00Z',
      updated_at: '2026-07-30T12:00:00Z',
    }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(userPayload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await getCurrentUser('test-access-token')

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/users/me',
      expect.objectContaining({
        credentials: 'omit',
        headers: expect.objectContaining({
          Authorization: 'Bearer test-access-token',
        }),
      }),
    )
  })
})
