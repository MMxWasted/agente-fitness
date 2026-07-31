import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './api'
import {
  BODY_MEASUREMENT_FILE_MAX_BYTES,
  previewBodyMeasurements,
  validateBodyMeasurementFile,
} from './body-measurement-import'
import { previewFixture } from '../test/body-measurement-preview-fixture'

beforeEach(() => {
  vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('body measurement import service', () => {
  it('sends multipart with bearer authentication and no cookies', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(previewFixture), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['synthetic'], 'measurements.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    const result = await previewBodyMeasurements(file)(
      'test-access-token-never-rendered',
    )

    expect(result).toEqual(previewFixture)
    const [url, options] = fetchMock.mock.calls[0] as [
      string,
      RequestInit,
    ]
    expect(url).toBe(
      'http://localhost:8000/api/v1/body-measurement-imports/preview',
    )
    expect(options.method).toBe('POST')
    expect(options.credentials).toBe('omit')
    expect(options.headers).toMatchObject({
      Accept: 'application/json',
      Authorization: 'Bearer test-access-token-never-rendered',
    })
    expect(options.headers).not.toHaveProperty('Content-Type')
    expect(options.body).toBeInstanceOf(FormData)
    const formData = options.body as FormData
    expect(formData.get('file')).toBe(file)
    expect([...formData.keys()]).toEqual(['file'])
    expect(String(options.body)).not.toContain(
      'test-access-token-never-rendered',
    )
  })

  it('validates extension, empty files, and the 5 MiB limit', () => {
    expect(
      validateBodyMeasurementFile(
        new File(['data'], 'measurements.csv'),
      ),
    ).toMatchObject({ valid: false })
    expect(
      validateBodyMeasurementFile(
        new File([], 'measurements.xlsx'),
      ),
    ).toMatchObject({ valid: false })
    const largeFile = new File(['data'], 'measurements.xlsx')
    Object.defineProperty(largeFile, 'size', {
      value: BODY_MEASUREMENT_FILE_MAX_BYTES + 1,
    })
    expect(validateBodyMeasurementFile(largeFile)).toMatchObject({
      valid: false,
    })
  })

  it('preserves controlled HTTP errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 415 })),
    )
    const request = previewBodyMeasurements(
      new File(['data'], 'measurements.xlsx'),
    )('test-access-token')

    await expect(request).rejects.toBeInstanceOf(ApiError)
    await expect(request).rejects.toHaveProperty('status', 415)
  })

  it('rejects a response that does not match the contract', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ fingerprint: 'not-complete' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(
      previewBodyMeasurements(
        new File(['data'], 'measurements.xlsx'),
      )('test-access-token'),
    ).rejects.toThrow('does not match the contract')
  })
})
