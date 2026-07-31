import {
  ApiError,
  getApiBaseUrl,
  type AuthenticatedOperation,
} from './api'

export type ExperienceLevel =
  | 'beginner'
  | 'intermediate'
  | 'advanced'
export type UnitSystem = 'metric' | 'imperial'

export interface FitnessProfile {
  id: string
  display_name: string
  birth_date: string | null
  height_cm: number | null
  experience_level: ExperienceLevel
  timezone: string
  unit_system: UnitSystem
  created_at: string
  updated_at: string
}

export interface ProfileInput {
  display_name: string
  birth_date: string | null
  height_cm: number | null
  experience_level: ExperienceLevel
  timezone: string
  unit_system: UnitSystem
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === 'string'
}

function isNullableNumber(value: unknown): value is number | null {
  return (
    value === null ||
    (typeof value === 'number' && Number.isFinite(value))
  )
}

function isExperienceLevel(
  value: unknown,
): value is ExperienceLevel {
  return ['beginner', 'intermediate', 'advanced'].includes(
    String(value),
  )
}

function isUnitSystem(value: unknown): value is UnitSystem {
  return value === 'metric' || value === 'imperial'
}

function isFitnessProfile(value: unknown): value is FitnessProfile {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    typeof value.id === 'string' &&
    'display_name' in value &&
    typeof value.display_name === 'string' &&
    'birth_date' in value &&
    isNullableString(value.birth_date) &&
    'height_cm' in value &&
    isNullableNumber(value.height_cm) &&
    'experience_level' in value &&
    isExperienceLevel(value.experience_level) &&
    'timezone' in value &&
    typeof value.timezone === 'string' &&
    'unit_system' in value &&
    isUnitSystem(value.unit_system) &&
    'created_at' in value &&
    typeof value.created_at === 'string' &&
    'updated_at' in value &&
    typeof value.updated_at === 'string'
  )
}

async function readProfileResponse(
  response: Response,
): Promise<FitnessProfile> {
  if (!response.ok) {
    throw new ApiError(response.status, 'Profile request failed')
  }

  const payload: unknown = await response.json()
  if (!isFitnessProfile(payload)) {
    throw new Error('Profile response does not match the contract')
  }
  return payload
}

export const getProfile: AuthenticatedOperation<FitnessProfile> =
  async (accessToken) => {
    const response = await fetch(`${getApiBaseUrl()}/api/v1/profile`, {
      credentials: 'omit',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
    })
    return readProfileResponse(response)
  }

export function putProfile(
  profile: ProfileInput,
): AuthenticatedOperation<FitnessProfile> {
  return async (accessToken) => {
    const response = await fetch(
      `${getApiBaseUrl()}/api/v1/profile`,
      {
        method: 'PUT',
        credentials: 'omit',
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profile),
      },
    )
    return readProfileResponse(response)
  }
}
