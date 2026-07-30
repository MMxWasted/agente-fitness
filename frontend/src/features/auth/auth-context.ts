import { createContext } from 'react'
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
}

export const AuthenticationContext =
  createContext<AuthenticationContextValue | null>(null)
