import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './api'
import {
  getProfile,
  putProfile,
  type FitnessProfile,
  type ProfileInput,
} from './profile'

const profile: FitnessProfile = {
  id: '62f53691-9b15-4ac5-8242-84b67dc53cbe',
  display_name: 'Alex',
  birth_date: '1995-05-12',
  height_cm: 178.25,
  experience_level: 'intermediate',
  timezone: 'Europe/Madrid',
  unit_system: 'metric',
  created_at: '2026-07-30T12:00:00Z',
  updated_at: '2026-07-30T12:00:00Z',
}

const profileInput: ProfileInput = {
  display_name: 'Alex',
  birth_date: '1995-05-12',
  height_cm: 178.25,
  experience_level: 'intermediate',
  timezone: 'Europe/Madrid',
  unit_system: 'metric',
}

beforeEach(() => {
  vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('profile service', () => {
  it('gets the profile with bearer authentication and no cookies', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(profile), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await getProfile('test-access-token')

    expect(result).toEqual(profile)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/profile',
      expect.objectContaining({
        credentials: 'omit',
        headers: expect.objectContaining({
          Authorization: 'Bearer test-access-token',
        }),
      }),
    )
  })

  it('replaces the complete profile without an owner identifier', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(profile), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await putProfile(profileInput)('test-access-token')

    const [, options] = fetchMock.mock.calls[0] as [
      string,
      RequestInit,
    ]
    expect(options.method).toBe('PUT')
    expect(options.credentials).toBe('omit')
    expect(options.headers).toMatchObject({
      Authorization: 'Bearer test-access-token',
      'Content-Type': 'application/json',
    })
    expect(JSON.parse(String(options.body))).toEqual(profileInput)
    expect(String(options.body)).not.toContain('user_id')
  })

  it('preserves controlled HTTP errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 404 })),
    )

    const request = getProfile('test-access-token')
    await expect(request).rejects.toBeInstanceOf(ApiError)
    await expect(request).rejects.toHaveProperty('status', 404)
  })

  it('rejects a response that does not match the contract', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ ...profile, height_cm: '178' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(getProfile('test-access-token')).rejects.toThrow(
      'Profile response does not match the contract',
    )
  })
})
