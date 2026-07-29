import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { checkApiHealth } from './services/health'

vi.mock('./services/health', () => ({
  checkApiHealth: vi.fn(),
}))

const checkApiHealthMock = vi.mocked(checkApiHealth)

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('App', () => {
  it('renders the technical foundation and checking state', () => {
    checkApiHealthMock.mockReturnValue(new Promise(() => undefined))

    render(<App />)

    expect(
      screen.getByRole('heading', { level: 1, name: 'Agente Fitness' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Fase 2 · Fundación técnica')).toBeVisible()
    expect(screen.getByText('Comprobando API')).toBeVisible()
  })

  it('shows the available state when the API responds successfully', async () => {
    checkApiHealthMock.mockResolvedValue({ status: 'ok' })

    render(<App />)

    expect(await screen.findByText('API disponible')).toBeVisible()
  })

  it('shows the unavailable state when the API request fails', async () => {
    checkApiHealthMock.mockRejectedValue(new Error('Network error'))

    render(<App />)

    expect(await screen.findByText('API no disponible')).toBeVisible()
  })
})
