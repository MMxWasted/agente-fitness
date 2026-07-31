import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import {
  getCurrentUser,
  login as requestLogin,
  logoutSession,
  refreshAccessToken,
  type AccessTokenResponse,
  type AuthenticatedUser,
} from '../../services/auth'
import {
  ApiError,
  type AuthenticatedOperation,
} from '../../services/api'
import {
  AuthenticationContext,
  type AuthenticationStatus,
} from './auth-context'

interface AuthenticationProviderProps {
  children: ReactNode
}

type RestoreResult =
  | {
      kind: 'authenticated'
      token: AccessTokenResponse
      user: AuthenticatedUser
    }
  | { kind: 'anonymous' }
  | { kind: 'expired' }

async function restoreSession(): Promise<RestoreResult> {
  let token: AccessTokenResponse
  try {
    token = await refreshAccessToken()
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return { kind: 'anonymous' }
    }
    throw error
  }

  try {
    const user = await getCurrentUser(token.access_token)
    return { kind: 'authenticated', token, user }
  } catch (error) {
    if (error instanceof ApiError && [401, 403].includes(error.status)) {
      return { kind: 'expired' }
    }
    throw error
  }
}

export function AuthenticationProvider({
  children,
}: AuthenticationProviderProps) {
  const [status, setStatus] = useState<AuthenticationStatus>('loading')
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const accessTokenRef = useRef<string | null>(null)
  const renewalTimerRef = useRef<number | null>(null)
  const renewRef = useRef<() => Promise<void>>(async () => undefined)
  const restorePromiseRef = useRef<Promise<RestoreResult> | null>(null)

  const clearRenewalTimer = useCallback(() => {
    if (renewalTimerRef.current !== null) {
      window.clearTimeout(renewalTimerRef.current)
      renewalTimerRef.current = null
    }
  }, [])

  const clearLocalSession = useCallback(() => {
    clearRenewalTimer()
    accessTokenRef.current = null
    setUser(null)
    setStatus('anonymous')
  }, [clearRenewalTimer])

  const expireLocalSession = useCallback(() => {
    clearLocalSession()
    setMessage(
      'La sesión ha expirado. Inicia sesión de nuevo para continuar.',
    )
  }, [clearLocalSession])

  const scheduleRenewal = useCallback(
    (expiresInSeconds: number) => {
      clearRenewalTimer()
      const renewalDelay = Math.max(1, expiresInSeconds - 30) * 1000
      renewalTimerRef.current = window.setTimeout(() => {
        void renewRef.current()
      }, renewalDelay)
    },
    [clearRenewalTimer],
  )

  const activateSession = useCallback(
    (token: AccessTokenResponse, currentUser: AuthenticatedUser) => {
      accessTokenRef.current = token.access_token
      setUser(currentUser)
      setStatus('authenticated')
      setMessage(null)
      scheduleRenewal(token.expires_in)
    },
    [scheduleRenewal],
  )

  renewRef.current = async () => {
    try {
      const token = await refreshAccessToken()
      accessTokenRef.current = token.access_token
      scheduleRenewal(token.expires_in)
    } catch {
      expireLocalSession()
    }
  }

  useEffect(() => {
    if (restorePromiseRef.current === null) {
      restorePromiseRef.current = restoreSession()
    }
    const restorePromise = restorePromiseRef.current
    let active = true

    void restorePromise
      .then((result) => {
        if (!active) {
          return
        }
        if (result.kind === 'authenticated') {
          activateSession(result.token, result.user)
          return
        }
        clearLocalSession()
        if (result.kind === 'expired') {
          setMessage(
            'La sesión ha expirado. Inicia sesión de nuevo para continuar.',
          )
        }
      })
      .catch(() => {
        if (active) {
          clearLocalSession()
          setMessage(
            'No se pudo comprobar la sesión. Revisa la conexión e inténtalo de nuevo.',
          )
        }
      })

    return () => {
      active = false
    }
  }, [activateSession, clearLocalSession])

  useEffect(() => clearRenewalTimer, [clearRenewalTimer])

  const login = useCallback(
    async (email: string, password: string) => {
      setIsSubmitting(true)
      setMessage(null)
      try {
        const token = await requestLogin(email, password)
        const currentUser = await getCurrentUser(token.access_token)
        activateSession(token, currentUser)
      } catch (error) {
        clearLocalSession()
        if (error instanceof ApiError && error.status === 401) {
          setMessage('El correo o la contraseña no son correctos.')
        } else {
          setMessage(
            'No se pudo iniciar sesión. Revisa la conexión e inténtalo de nuevo.',
          )
        }
      } finally {
        setIsSubmitting(false)
      }
    },
    [activateSession, clearLocalSession],
  )

  const logout = useCallback(async () => {
    setIsSubmitting(true)
    setMessage(null)
    try {
      await logoutSession()
      clearLocalSession()
    } catch {
      clearLocalSession()
      setMessage(
        'La sesión local se cerró, pero no se pudo confirmar la revocación en el servidor.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }, [clearLocalSession])

  const authenticatedRequest = useCallback(
    async <T,>(
      operation: AuthenticatedOperation<T>,
    ): Promise<T> => {
      const currentAccessToken = accessTokenRef.current
      if (currentAccessToken === null) {
        expireLocalSession()
        throw new ApiError(401, 'Authentication required')
      }

      try {
        return await operation(currentAccessToken)
      } catch (error) {
        if (!(error instanceof ApiError)) {
          throw error
        }
        if (error.status === 403) {
          expireLocalSession()
          throw error
        }
        if (error.status !== 401) {
          throw error
        }
      }

      let token: AccessTokenResponse
      try {
        token = await refreshAccessToken()
      } catch {
        expireLocalSession()
        throw new ApiError(401, 'Session expired')
      }

      accessTokenRef.current = token.access_token
      scheduleRenewal(token.expires_in)
      try {
        return await operation(token.access_token)
      } catch (error) {
        if (
          error instanceof ApiError &&
          [401, 403].includes(error.status)
        ) {
          expireLocalSession()
        }
        throw error
      }
    },
    [expireLocalSession, scheduleRenewal],
  )

  const contextValue = useMemo(
    () => ({
      status,
      user,
      message,
      isSubmitting,
      login,
      logout,
      authenticatedRequest,
    }),
    [
      authenticatedRequest,
      isSubmitting,
      login,
      logout,
      message,
      status,
      user,
    ],
  )

  return (
    <AuthenticationContext value={contextValue}>
      {children}
    </AuthenticationContext>
  )
}
