import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../services/api'
import {
  BODY_MEASUREMENT_FILE_MAX_BYTES,
  type BodyMeasurementImportPreview as PreviewResult,
} from '../../services/body-measurement-import'
import type {
  BodyMeasurementImportPlan,
  BodyMeasurementImportRecord,
  BodyMeasurementReview,
  BodyMeasurementReviewDetail,
  BodyMeasurementSource,
} from '../../services/body-measurement-history'
import { previewFixture } from '../../test/body-measurement-preview-fixture'
import {
  AuthenticationContext,
  type AuthenticationContextValue,
} from '../auth/auth-context'
import { BodyMeasurementImportPreview } from './BodyMeasurementImportPreview'

const accessToken = 'test-access-token-never-rendered'
const authenticatedRequest: AuthenticationContextValue['authenticatedRequest'] =
  async (operation) => operation(accessToken)

const contextValue: AuthenticationContextValue = {
  status: 'authenticated',
  user: {
    id: '68f05028-d75e-4bc1-8db2-520355f10331',
    email: 'person@example.com',
    is_active: true,
    created_at: '2026-07-30T12:00:00Z',
    updated_at: '2026-07-30T12:00:00Z',
  },
  message: null,
  isSubmitting: false,
  login: async () => undefined,
  logout: async () => undefined,
  authenticatedRequest,
}

function renderPreview(
  request: AuthenticationContextValue['authenticatedRequest'] =
    authenticatedRequest,
) {
  return render(
    <AuthenticationContext
      value={{ ...contextValue, authenticatedRequest: request }}
    >
      <BodyMeasurementImportPreview />
    </AuthenticationContext>,
  )
}

function selectValidFile() {
  const file = new File(['synthetic'], 'measurements.xlsx', {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  fireEvent.change(screen.getByLabelText('Archivo Excel', { exact: false }), {
    target: { files: [file] },
  })
  return file
}

function successfulRequest(
  result: PreviewResult = previewFixture,
): AuthenticationContextValue['authenticatedRequest'] {
  return requestAfterHistory(async () => result)
}

const source: BodyMeasurementSource = {
  id: '2da35ae6-9704-4e79-9a5a-dce6ce3309dd',
  display_name: 'Revisiones Excel',
  source_kind: 'manual_excel',
  logical_key: 'excel-principal',
  history_version: 0,
  created_at: '2026-07-31T10:00:00Z',
  updated_at: '2026-07-31T10:00:00Z',
}

function requestAfterHistory(
  operation: () => Promise<unknown>,
): AuthenticationContextValue['authenticatedRequest'] {
  let call = 0
  return async <T,>() => {
    call += 1
    if (call === 1) {
      return { items: [source], total: 1, limit: 100, offset: 0 } as T
    }
    if (call === 2 || call === 3) {
      return { items: [], total: 0, limit: 100, offset: 0 } as T
    }
    return (await operation()) as T
  }
}

function requestSequence(
  responses: unknown[],
): AuthenticationContextValue['authenticatedRequest'] {
  let call = 0
  return async <T,>() => {
    call += 1
    if (call === 1 || call === 7) {
      return { items: [source], total: 1, limit: 100, offset: 0 } as T
    }
    if ([2, 3, 8, 9].includes(call)) {
      return { items: [], total: 0, limit: 100, offset: 0 } as T
    }
    const response = responses.shift()
    if (response instanceof Error) throw response
    return response as T
  }
}

function requestTimeline(
  responses: unknown[],
): AuthenticationContextValue['authenticatedRequest'] {
  return async <T,>() => {
    const response = responses.shift()
    if (response instanceof Error) throw response
    return response as T
  }
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('BodyMeasurementImportPreview', () => {
  it('renders an accessible selector and validates type and size', () => {
    renderPreview()
    const input = screen.getByLabelText('Archivo Excel', {
      exact: false,
    })
    expect(input).toHaveAttribute('type', 'file')
    expect(input).toHaveAttribute('accept', expect.stringContaining('.xlsx'))

    fireEvent.change(input, {
      target: { files: [new File(['data'], 'measurements.csv')] },
    })
    expect(
      screen.getByText('Selecciona un archivo .xlsx sin macros.'),
    ).toBeVisible()

    const largeFile = new File(['data'], 'measurements.xlsx')
    Object.defineProperty(largeFile, 'size', {
      value: BODY_MEASUREMENT_FILE_MAX_BYTES + 1,
    })
    fireEvent.change(input, { target: { files: [largeFile] } })
    expect(
      screen.getByText('El archivo supera el límite de 5 MiB.'),
    ).toBeVisible()
  })

  it('shows the analyzing state while the authenticated request is pending', () => {
    const pendingRequest: AuthenticationContextValue['authenticatedRequest'] =
      async () => new Promise(() => undefined)
    renderPreview(pendingRequest)
    selectValidFile()

    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))

    expect(
      screen.getByText('Analizando el archivo de forma segura…'),
    ).toBeVisible()
    expect(screen.getByRole('button', { name: 'Analizando…' })).toBeDisabled()
  })

  it('groups a valid preview and shows warnings, errors, and unknown metrics', async () => {
    const storageWrite = vi.spyOn(Storage.prototype, 'setItem')
    renderPreview(successfulRequest())
    selectValidFile()
    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))

    expect(
      await screen.findByText('Resumen de la previsualización'),
    ).toBeVisible()
    expect(screen.getByText('Revisión 2026-01-15')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Bioimpedancia' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Perímetros' })).toBeVisible()
    expect(screen.getByText('Peso corporal')).toBeVisible()
    expect(screen.getByText('Muslo izquierdo')).toBeVisible()
    expect(screen.getByText('Falta el año de una revisión.')).toBeVisible()
    expect(
      screen.getByText('Año propuesto, todavía sin resolver.'),
    ).toBeVisible()
    expect(
      screen.getByRole('checkbox', {
        name: /Excluir .*ndice experimental.*Otros/,
      }),
    ).toBeVisible()
    expect(document.body.textContent).not.toContain(accessToken)
    expect(storageWrite).not.toHaveBeenCalled()
    storageWrite.mockRestore()
  })

  it.each([
    [
      new ApiError(422, 'Invalid workbook'),
      'Hay decisiones pendientes o el archivo no coincide con el formato compatible.',
    ],
    [
      new ApiError(401, 'Expired'),
      'La sesión ha expirado. Inicia sesión de nuevo.',
    ],
    [
      new Error('Network unavailable'),
      'No se pudo conectar con la API. Revisa la conexión e inténtalo de nuevo.',
    ],
  ])('shows a controlled analysis error', async (error, expectedMessage) => {
    const failingRequest = requestAfterHistory(async () => {
      throw error
    })
    renderPreview(failingRequest)
    selectValidFile()
    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))

    expect(await screen.findByText(expectedMessage)).toBeVisible()
  })

  it('retries the same in-memory file after a network error', async () => {
    let attempt = 0
    const retryingRequest = requestAfterHistory(async () => {
        attempt += 1
        if (attempt === 1) {
          throw new Error('Network unavailable')
        }
        return previewFixture
      })
    renderPreview(retryingRequest)
    selectValidFile()
    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))
    await screen.findByText(
      'No se pudo conectar con la API. Revisa la conexión e inténtalo de nuevo.',
    )

    fireEvent.click(screen.getByRole('button', { name: 'Reintentar análisis' }))

    expect(
      await screen.findByText('Resumen de la previsualización'),
    ).toBeVisible()
    expect(attempt).toBe(2)
  })

  it('clears the preview when selecting another file', async () => {
    renderPreview(successfulRequest())
    selectValidFile()
    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))
    await screen.findByText('Resumen de la previsualización')

    fireEvent.click(
      screen.getByRole('button', { name: 'Seleccionar otro archivo' }),
    )

    await waitFor(() => {
      expect(
        screen.queryByText('Resumen de la previsualización'),
      ).not.toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Analizar archivo' })).toBeDisabled()
  })

  it('plans and explicitly confirms a new import', async () => {
    const plan: BodyMeasurementImportPlan = {
      source_id: source.id,
      history_version: 0,
      confirmed_fingerprint: `sha256:${'b'.repeat(64)}`,
      revisions: [
        {
          revision_index: 0,
          label: '2026-01-15',
          measurement_date: '2026-01-15',
          disambiguator: '',
          classification: 'new',
          metric_count: 2,
          current_review_id: null,
          current_version: null,
          issues: [],
        },
      ],
      totals: { new: 1, identical: 0, modified: 0, blocked: 0, excluded: 0 },
    }
    const imported: BodyMeasurementImportRecord = {
      id: '94f380ea-ccaa-4f2f-8505-8b4143e3a09c',
      source_id: source.id,
      status: 'completed',
      adapter_version: 'body-measurements-v1',
      outcome: 'created',
      created_review_count: 1,
      skipped_review_count: 0,
      versioned_review_count: 0,
      excluded_review_count: 0,
      imported_at: '2026-07-31T12:00:00Z',
      reverted_at: null,
    }
    renderPreview(requestSequence([previewFixture, plan, imported]))
    selectValidFile()
    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))
    await screen.findByText('Resumen de la previsualización')

    fireEvent.click(
      screen.getByRole('checkbox', {
        name: /Excluir .*ndice experimental/,
      }),
    )
    fireEvent.click(
      screen.getByRole('button', { name: 'Calcular plan de importación' }),
    )

    expect(await screen.findByText(/Nuevas: 1/)).toBeVisible()
    fireEvent.click(
      screen.getByRole('checkbox', {
        name: 'Confirmo que he revisado el plan y deseo persistirlo',
      }),
    )
    fireEvent.click(
      screen.getByRole('button', { name: 'Confirmar importación' }),
    )

    expect(
      await screen.findByText(/Resultado: created/),
    ).toBeVisible()
  })

  it('requires explicit immutable versioning for a modified revision', async () => {
    const modifiedPlan: BodyMeasurementImportPlan = {
      source_id: source.id,
      history_version: 3,
      confirmed_fingerprint: `sha256:${'c'.repeat(64)}`,
      revisions: [
        {
          revision_index: 0,
          label: '2026-01-15',
          measurement_date: '2026-01-15',
          disambiguator: '',
          classification: 'modified',
          metric_count: 2,
          current_review_id: '680ca987-ec17-4487-bbb8-c3d33206e730',
          current_version: 1,
          issues: [],
        },
      ],
      totals: { new: 0, identical: 0, modified: 1, blocked: 0, excluded: 0 },
    }
    renderPreview(requestSequence([previewFixture, modifiedPlan]))
    selectValidFile()
    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))
    await screen.findByText('Resumen de la previsualización')
    fireEvent.click(
      screen.getByRole('button', { name: 'Calcular plan de importación' }),
    )

    const confirmation = await screen.findByRole('checkbox', {
      name: 'Confirmo que he revisado el plan y deseo persistirlo',
    })
    expect(confirmation).toBeDisabled()
    fireEvent.click(
      screen.getByRole('checkbox', {
        name: 'Crear una nueva versión inmutable',
      }),
    )
    expect(confirmation).toBeEnabled()
  })

  it('keeps one idempotency key while retrying a failed confirmation', async () => {
    const plan: BodyMeasurementImportPlan = {
      source_id: source.id,
      history_version: 0,
      confirmed_fingerprint: `sha256:${'d'.repeat(64)}`,
      revisions: [],
      totals: { new: 0, identical: 1, modified: 0, blocked: 0, excluded: 0 },
    }
    const imported: BodyMeasurementImportRecord = {
      id: '94f380ea-ccaa-4f2f-8505-8b4143e3a09c',
      source_id: source.id,
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
    const sourcePage = { items: [source], total: 1, limit: 100, offset: 0 }
    const emptyPage = { items: [], total: 0, limit: 100, offset: 0 }
    const randomUuid = vi.spyOn(crypto, 'randomUUID').mockReturnValue(
      '5ea94a55-4ecb-453d-89ac-e228c8af49d8',
    )
    renderPreview(
      requestTimeline([
        sourcePage,
        emptyPage,
        emptyPage,
        previewFixture,
        plan,
        new Error('Network unavailable'),
        imported,
        sourcePage,
        emptyPage,
        emptyPage,
      ]),
    )
    selectValidFile()
    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))
    await screen.findByText('Resumen de la previsualización')
    fireEvent.click(
      screen.getByRole('button', { name: 'Calcular plan de importación' }),
    )
    const confirmation = await screen.findByRole('checkbox', {
      name: 'Confirmo que he revisado el plan y deseo persistirlo',
    })
    fireEvent.click(confirmation)
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar importación' }))
    await screen.findByText(
      'No se pudo conectar con la API. Revisa la conexión e inténtalo de nuevo.',
    )

    fireEvent.click(screen.getByRole('button', { name: 'Confirmar importación' }))
    expect(await screen.findByText(/Resultado: skipped/)).toBeVisible()
    expect(randomUuid).toHaveBeenCalledTimes(1)
  })

  it('loads detail and explicitly reverts an owned import', async () => {
    const measurementImport: BodyMeasurementImportRecord = {
      id: '94f380ea-ccaa-4f2f-8505-8b4143e3a09c',
      source_id: source.id,
      status: 'completed',
      adapter_version: 'body-measurements-v1',
      outcome: 'created',
      created_review_count: 1,
      skipped_review_count: 0,
      versioned_review_count: 0,
      excluded_review_count: 0,
      imported_at: '2026-07-31T12:00:00Z',
      reverted_at: null,
    }
    const review: BodyMeasurementReview = {
      id: '680ca987-ec17-4487-bbb8-c3d33206e730',
      source_id: source.id,
      import_id: measurementImport.id,
      measurement_date: '2026-01-15',
      original_label: '2026-01-15',
      normalized_label: '2026-01-15',
      disambiguator: '',
      version: 1,
      supersedes_review_id: null,
      is_current: true,
      metric_count: 1,
      created_at: '2026-07-31T12:00:00Z',
    }
    const detail: BodyMeasurementReviewDetail = {
      ...review,
      values: [
        {
          id: 'a61dc5d2-8f92-4099-b198-1f27c32768e2',
          metric_code: 'body_weight',
          category: 'bioimpedance',
          side: 'none',
          value: '72.8',
          unit: 'kg',
          original_label: 'Peso corporal',
          origin: 'reported',
          catalog_version: 'body-measurements-v1',
        },
      ],
    }
    const sourcePage = { items: [source], total: 1, limit: 100, offset: 0 }
    const importPage = { items: [measurementImport], total: 1, limit: 100, offset: 0 }
    const reviewPage = { items: [review], total: 1, limit: 100, offset: 0 }
    const emptyPage = { items: [], total: 0, limit: 100, offset: 0 }
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    renderPreview(
      requestTimeline([
        sourcePage,
        importPage,
        reviewPage,
        detail,
        undefined,
        sourcePage,
        emptyPage,
        emptyPage,
      ]),
    )

    expect(await screen.findByText(/2026-01-15/)).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Ver detalle' }))
    expect(await screen.findByText('Peso corporal')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Revertir' }))

    expect(
      await screen.findByText('Importación revertida correctamente.'),
    ).toBeVisible()
    expect(window.confirm).toHaveBeenCalledTimes(1)
  })
})
