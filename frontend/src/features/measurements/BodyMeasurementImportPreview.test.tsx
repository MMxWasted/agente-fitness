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
  return async <T,>() => result as T
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
    expect(screen.getByText('Índice experimental · Otros')).toBeVisible()
    expect(document.body.textContent).not.toContain(accessToken)
    expect(storageWrite).not.toHaveBeenCalled()
    storageWrite.mockRestore()
  })

  it.each([
    [
      new ApiError(422, 'Invalid workbook'),
      'El archivo no coincide con el formato de revisiones compatible.',
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
    const failingRequest: AuthenticationContextValue['authenticatedRequest'] =
      async () => {
        throw error
      }
    renderPreview(failingRequest)
    selectValidFile()
    fireEvent.click(screen.getByRole('button', { name: 'Analizar archivo' }))

    expect(await screen.findByText(expectedMessage)).toBeVisible()
  })

  it('retries the same in-memory file after a network error', async () => {
    let attempt = 0
    const retryingRequest: AuthenticationContextValue['authenticatedRequest'] =
      async <T,>() => {
        attempt += 1
        if (attempt === 1) {
          throw new Error('Network unavailable')
        }
        return previewFixture as T
      }
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
})
