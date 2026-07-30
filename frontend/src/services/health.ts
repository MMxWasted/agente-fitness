import { getApiBaseUrl } from './api'

export interface HealthResponse {
  status: 'ok'
}

function isHealthResponse(value: unknown): value is HealthResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    value.status === 'ok'
  )
}

export async function checkApiHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getApiBaseUrl()}/health`, {
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`)
  }

  const payload: unknown = await response.json()

  if (!isHealthResponse(payload)) {
    throw new Error('Health response does not match the expected contract')
  }

  return payload
}
