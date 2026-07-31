import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { AuthenticationProvider } from './features/auth/AuthenticationProvider'
import {
  getCurrentUser,
  login,
  logoutSession,
  refreshAccessToken,
  type AccessTokenResponse,
  type AuthenticatedUser,
} from './services/auth'
import { ApiError } from './services/api'
import { checkApiHealth } from './services/health'

vi.mock('./services/health', () => ({
  checkApiHealth: vi.fn(),
}))

vi.mock('./services/auth', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logoutSession: vi.fn(),
  refreshAccessToken: vi.fn(),
}))

vi.mock('./features/profile/ProfileSection', () => ({
  ProfileSection: () => (
    <section aria-label="Perfil fitness de prueba" />
  ),
}))

const checkApiHealthMock = vi.mocked(checkApiHealth)
const getCurrentUserMock = vi.mocked(getCurrentUser)
const loginMock = vi.mocked(login)
const logoutSessionMock = vi.mocked(logoutSession)
const refreshAccessTokenMock = vi.mocked(refreshAccessToken)

const tokenResponse: AccessTokenResponse = {
  access_token: 'test-access-token-never-rendered',
  token_type: 'bearer',
  expires_in: 1800,
}

const authenticatedUser: AuthenticatedUser = {
  id: '68f05028-d75e-4bc1-8db2-520355f10331',
  email: 'person@example.com',
  is_active: true,
  created_at: '2026-07-30T12:00:00Z',
  updated_at: '2026-07-30T12:00:00Z',
}

function renderApp() {
  return render(
    <AuthenticationProvider>
      <App />
    </AuthenticationProvider>,
  )
}

beforeEach(() => {
  checkApiHealthMock.mockResolvedValue({ status: 'ok' })
  refreshAccessTokenMock.mockRejectedValue(
    new ApiError(401, 'No refresh cookie'),
  )
  logoutSessionMock.mockResolvedValue()
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('App authentication', () => {
  it('shows the initial session loading state', () => {
    refreshAccessTokenMock.mockReturnValue(new Promise(() => undefined))

    renderApp()

    expect(
      screen.getByRole('heading', { level: 1, name: 'Agente Fitness' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Comprobando sesión…')).toBeVisible()
  })

  it('renders an accessible login form for an anonymous user', async () => {
    renderApp()

    expect(
      await screen.findByRole('heading', { level: 2, name: 'Acceso' }),
    ).toBeVisible()
    expect(screen.getByLabelText('Correo electrónico')).toHaveAttribute(
      'type',
      'email',
    )
    expect(screen.getByLabelText('Contraseña')).toHaveAttribute(
      'type',
      'password',
    )
    expect(
      screen.getByRole('button', { name: 'Iniciar sesión' }),
    ).toBeEnabled()
  })

  it('logs in and keeps the access token out of the interface', async () => {
    loginMock.mockResolvedValue(tokenResponse)
    getCurrentUserMock.mockResolvedValue(authenticatedUser)
    renderApp()
    await screen.findByRole('button', { name: 'Iniciar sesión' })

    fireEvent.change(screen.getByLabelText('Correo electrónico'), {
      target: { value: '  person@example.com  ' },
    })
    fireEvent.change(screen.getByLabelText('Contraseña'), {
      target: { value: 'a-long-test-password' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(await screen.findByText('person@example.com')).toBeVisible()
    expect(loginMock).toHaveBeenCalledWith(
      'person@example.com',
      'a-long-test-password',
    )
    expect(getCurrentUserMock).toHaveBeenCalledWith(
      tokenResponse.access_token,
    )
    expect(document.body.textContent).not.toContain(
      tokenResponse.access_token,
    )
  })

  it('shows a generic invalid credentials error', async () => {
    loginMock.mockRejectedValue(new ApiError(401, 'Invalid credentials'))
    renderApp()
    await screen.findByRole('button', { name: 'Iniciar sesión' })

    fireEvent.change(screen.getByLabelText('Correo electrónico'), {
      target: { value: 'person@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Contraseña'), {
      target: { value: 'a-wrong-test-password' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(
      await screen.findByText(
        'El correo o la contraseña no son correctos.',
      ),
    ).toBeVisible()
  })

  it('restores a session and loads the current user', async () => {
    refreshAccessTokenMock.mockResolvedValue(tokenResponse)
    getCurrentUserMock.mockResolvedValue(authenticatedUser)

    renderApp()

    expect(await screen.findByText('person@example.com')).toBeVisible()
    expect(
      screen.getByRole('heading', { level: 2, name: 'Sesión activa' }),
    ).toBeVisible()
    expect(refreshAccessTokenMock).toHaveBeenCalledTimes(1)
  })

  it('reports an expired session when current identity is rejected', async () => {
    refreshAccessTokenMock.mockResolvedValue(tokenResponse)
    getCurrentUserMock.mockRejectedValue(
      new ApiError(401, 'Expired access token'),
    )

    renderApp()

    expect(
      await screen.findByText(
        'La sesión ha expirado. Inicia sesión de nuevo para continuar.',
      ),
    ).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Iniciar sesión' }),
    ).toBeVisible()
  })

  it('logs out and returns to the anonymous state', async () => {
    refreshAccessTokenMock.mockResolvedValue(tokenResponse)
    getCurrentUserMock.mockResolvedValue(authenticatedUser)
    renderApp()
    await screen.findByText('person@example.com')

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))

    await waitFor(() => {
      expect(logoutSessionMock).toHaveBeenCalledTimes(1)
    })
    expect(
      await screen.findByRole('button', { name: 'Iniciar sesión' }),
    ).toBeVisible()
  })

  it('shows a controlled network error during restoration', async () => {
    refreshAccessTokenMock.mockRejectedValue(new Error('Network unavailable'))

    renderApp()

    expect(
      await screen.findByText(
        'No se pudo comprobar la sesión. Revisa la conexión e inténtalo de nuevo.',
      ),
    ).toBeVisible()
  })

  it('never writes session credentials to web storage', async () => {
    const storageWrite = vi.spyOn(Storage.prototype, 'setItem')
    loginMock.mockResolvedValue(tokenResponse)
    getCurrentUserMock.mockResolvedValue(authenticatedUser)
    renderApp()
    await screen.findByRole('button', { name: 'Iniciar sesión' })

    fireEvent.change(screen.getByLabelText('Correo electrónico'), {
      target: { value: 'person@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Contraseña'), {
      target: { value: 'a-long-test-password' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))
    await screen.findByText('person@example.com')

    expect(storageWrite).not.toHaveBeenCalled()
    storageWrite.mockRestore()
  })
})

describe('App API status', () => {
  it('shows the available state when health succeeds', async () => {
    renderApp()

    expect(await screen.findByText('API disponible')).toBeVisible()
  })

  it('shows the unavailable state when health fails', async () => {
    checkApiHealthMock.mockRejectedValue(new Error('Network error'))

    renderApp()

    expect(await screen.findByText('API no disponible')).toBeVisible()
  })
})
