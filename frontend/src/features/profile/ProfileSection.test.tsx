import {
  cleanup,
  fireEvent,
  render,
  screen,
} from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../services/api'
import type { FitnessProfile } from '../../services/profile'
import {
  AuthenticationContext,
  type AuthenticationContextValue,
} from '../auth/auth-context'
import { ProfileSection } from './ProfileSection'

const accessToken = 'test-access-token-never-rendered'
const profile: FitnessProfile = {
  id: '62f53691-9b15-4ac5-8242-84b67dc53cbe',
  display_name: 'Alex',
  birth_date: '1995-05-12',
  height_cm: 180.34,
  experience_level: 'intermediate',
  timezone: 'Europe/Madrid',
  unit_system: 'metric',
  created_at: '2026-07-30T12:00:00Z',
  updated_at: '2026-07-30T12:00:00Z',
}

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

function renderProfileSection(
  request: AuthenticationContextValue['authenticatedRequest'] =
    authenticatedRequest,
) {
  return render(
    <AuthenticationContext
      value={{ ...contextValue, authenticatedRequest: request }}
    >
      <ProfileSection />
    </AuthenticationContext>,
  )
}

function response(
  body: unknown,
  status = 200,
): Response {
  return new Response(
    body === null ? null : JSON.stringify(body),
    {
      status,
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

beforeEach(() => {
  vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('ProfileSection', () => {
  it('shows the initial loading state', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)))

    renderProfileSection()

    expect(screen.getByText('Cargando perfil…')).toBeVisible()
  })

  it('shows an accessible creation form when the profile is missing', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(null, 404)))

    renderProfileSection()

    expect(
      await screen.findByText('Todavía no tienes perfil.', {
        exact: false,
      }),
    ).toBeVisible()
    expect(screen.getByLabelText('Nombre visible')).toBeRequired()
    expect(screen.getByLabelText('Nivel de experiencia')).toBeRequired()
    expect(screen.getByLabelText('Zona horaria IANA')).toBeRequired()
    expect(screen.getByLabelText('Sistema de unidades')).toBeRequired()
  })

  it('creates a profile and keeps the bearer out of storage and the DOM', async () => {
    const storageWrite = vi.spyOn(Storage.prototype, 'setItem')
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(null, 404))
      .mockResolvedValueOnce(response(profile))
    vi.stubGlobal('fetch', fetchMock)
    renderProfileSection()
    await screen.findByLabelText('Nombre visible')

    fireEvent.change(screen.getByLabelText('Nombre visible'), {
      target: { value: '  Alex  ' },
    })
    fireEvent.change(screen.getByLabelText('Nivel de experiencia'), {
      target: { value: 'intermediate' },
    })
    fireEvent.change(screen.getByLabelText('Sistema de unidades'), {
      target: { value: 'metric' },
    })
    fireEvent.change(screen.getByLabelText('Altura (cm) (opcional)'), {
      target: { value: '180.34' },
    })
    fireEvent.change(screen.getByLabelText('Zona horaria IANA'), {
      target: { value: 'Europe/Madrid' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar perfil' }))

    expect(
      await screen.findByText('Perfil guardado correctamente.'),
    ).toBeVisible()
    const [, options] = fetchMock.mock.calls[1] as [
      string,
      RequestInit,
    ]
    expect(options.credentials).toBe('omit')
    expect(options.headers).toMatchObject({
      Authorization: `Bearer ${accessToken}`,
    })
    expect(JSON.parse(String(options.body))).toMatchObject({
      display_name: 'Alex',
      height_cm: 180.34,
    })
    expect(document.body.textContent).not.toContain(accessToken)
    expect(storageWrite).not.toHaveBeenCalled()
  })

  it('loads, edits and converts imperial height back to centimeters', async () => {
    const imperialProfile: FitnessProfile = {
      ...profile,
      unit_system: 'imperial',
    }
    const savedProfile = {
      ...imperialProfile,
      display_name: 'Updated',
      height_cm: 177.8,
      updated_at: '2026-07-30T13:00:00Z',
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(imperialProfile))
      .mockResolvedValueOnce(response(savedProfile))
    vi.stubGlobal('fetch', fetchMock)
    renderProfileSection()

    expect(await screen.findByText('Alex')).toBeVisible()
    expect(screen.getByText('5 ft 11 in')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Editar perfil' }))
    fireEvent.change(screen.getByLabelText('Nombre visible'), {
      target: { value: 'Updated' },
    })
    fireEvent.change(
      screen.getByLabelText('Altura (pulgadas) (opcional)'),
      { target: { value: '70' } },
    )
    fireEvent.click(screen.getByRole('button', { name: 'Guardar perfil' }))

    expect(await screen.findByText('Updated')).toBeVisible()
    const submitted = JSON.parse(
      String(
        (fetchMock.mock.calls[1][1] as RequestInit).body,
      ),
    ) as { height_cm: number }
    expect(submitted.height_cm).toBe(177.8)
  })

  it('shows client-side validation messages before sending', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(null, 404))
    vi.stubGlobal('fetch', fetchMock)
    renderProfileSection()
    await screen.findByLabelText('Nombre visible')

    fireEvent.click(screen.getByRole('button', { name: 'Guardar perfil' }))

    expect(
      screen.getByText(
        'El nombre visible debe tener entre 1 y 80 caracteres.',
      ),
    ).toBeVisible()
    expect(
      screen.getByText('Selecciona un nivel de experiencia.'),
    ).toBeVisible()
    expect(
      screen.getByText('Indica una zona horaria IANA.'),
    ).toBeVisible()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('shows backend and network errors with a retry path', async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error('Network unavailable'))
      .mockResolvedValueOnce(response(null, 404))
    vi.stubGlobal('fetch', fetchMock)
    renderProfileSection()

    expect(
      await screen.findByText(
        'No se pudo cargar el perfil. Revisa la conexión e inténtalo de nuevo.',
      ),
    ).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByLabelText('Nombre visible')).toBeVisible()
  })

  it('shows a controlled message when the session expires', async () => {
    const expiredRequest: AuthenticationContextValue['authenticatedRequest'] =
      async () => {
        throw new ApiError(401, 'Expired')
      }

    renderProfileSection(expiredRequest)

    expect(
      await screen.findByText(
        'La sesión ha expirado. Inicia sesión de nuevo.',
      ),
    ).toBeVisible()
  })

  it('shows a controlled validation error returned by the backend', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(null, 404))
      .mockResolvedValueOnce(response({ detail: [] }, 422))
    vi.stubGlobal('fetch', fetchMock)
    renderProfileSection()
    await screen.findByLabelText('Nombre visible')

    fireEvent.change(screen.getByLabelText('Nombre visible'), {
      target: { value: 'Alex' },
    })
    fireEvent.change(screen.getByLabelText('Nivel de experiencia'), {
      target: { value: 'beginner' },
    })
    fireEvent.change(screen.getByLabelText('Sistema de unidades'), {
      target: { value: 'metric' },
    })
    fireEvent.change(screen.getByLabelText('Zona horaria IANA'), {
      target: { value: 'Invalid/Timezone' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar perfil' }))

    expect(
      await screen.findByText(
        'El servidor rechazó algún valor. Revisa los campos del perfil.',
      ),
    ).toBeVisible()
  })
})
