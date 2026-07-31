import { createContext } from 'react'
import type { AuthenticatedOperation } from '../../services/api'
import type { AuthenticatedUser } from '../../services/auth'

export type AuthenticationStatus =
  | 'loading'
  | 'anonymous'
  | 'authenticated'

export interface AuthenticationContextValue {
  status: AuthenticationStatus
  user: AuthenticatedUser | null
  message: string | null
  isSubmitting: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  authenticatedRequest: <T>(
    operation: AuthenticatedOperation<T>,
  ) => Promise<T>
}

export const AuthenticationContext =
  createContext<AuthenticationContextValue | null>(null)
