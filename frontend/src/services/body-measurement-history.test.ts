import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './api'
import {
  confirmBodyMeasurementImport,
  emptyImportDecisions,
  listBodyMeasurementSources,
  revertBodyMeasurementImport,
  type BodyMeasurementImportPlan,
  type BodyMeasurementImportRecord,
} from './body-measurement-history'
import { previewFixture } from '../test/body-measurement-preview-fixture'

const sourceId = '2da35ae6-9704-4e79-9a5a-dce6ce3309dd'
const plan: BodyMeasurementImportPlan = {
  source_id: sourceId,
  history_version: 4,
  confirmed_fingerprint: `sha256:${'b'.repeat(64)}`,
  revisions: [],
  totals: { new: 0, identical: 0, modified: 0, blocked: 0, excluded: 0 },
}
const imported: BodyMeasurementImportRecord = {
  id: '94f380ea-ccaa-4f2f-8505-8b4143e3a09c',
  source_id: sourceId,
  status: 'completed',
  adapter_version: 'body-measurements-v1',
  outcome: 'skipped',
  created_review_count: 0,
  skipped_review_count: 1,
  versioned_review_count: 0,
  excluded_review_count: 0,
  imported_at: '2026-07-31T12:00:00Z',
  reverted_at: null,
}

beforeEach(() => {
  vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('body measurement history service', () => {
  it('confirms with multipart decisions and caller-owned idempotency key', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(imported), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['synthetic'], 'measurements.xlsx')
    const decisions = emptyImportDecisions()

    const result = await confirmBodyMeasurementImport(
      file,
      sourceId,
      previewFixture,
      plan,
      decisions,
      'stable-retry-key-0001',
    )('access-token-never-rendered')

    expect(result).toEqual(imported)
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(
      'http://localhost:8000/api/v1/body-measurement-imports',
    )
    expect(options.credentials).toBe('omit')
    expect(options.headers).toMatchObject({
      Authorization: 'Bearer access-token-never-rendered',
      'Idempotency-Key': 'stable-retry-key-0001',
    })
    expect(options.headers).not.toHaveProperty('Content-Type')
    const formData = options.body as FormData
    expect(formData.get('file')).toBe(file)
    expect(formData.get('source_id')).toBe(sourceId)
    expect(formData.get('history_version')).toBe('4')
    expect(formData.get('confirmed_fingerprint')).toBe(
      plan.confirmed_fingerprint,
    )
    expect(JSON.parse(String(formData.get('decisions')))).toEqual(decisions)
    expect([...formData.keys()]).not.toContain('values')
  })

  it('lists sources using bearer auth and no cookies', async () => {
    const page = { items: [], total: 0, limit: 100, offset: 0 }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(page), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(listBodyMeasurementSources('access-token')).resolves.toEqual(page)
    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(options.credentials).toBe('omit')
    expect(options.headers).toMatchObject({
      Authorization: 'Bearer access-token',
    })
  })

  it('maps reversal conflicts without leaking response bodies', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'private database detail' }), {
          status: 409,
        }),
      ),
    )

    const request = revertBodyMeasurementImport(imported.id)('access-token')
    await expect(request).rejects.toBeInstanceOf(ApiError)
    await expect(request).rejects.toMatchObject({
      status: 409,
      message: 'Body measurement reversal failed',
    })
  })
})
