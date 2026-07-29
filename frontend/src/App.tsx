import { useEffect, useState } from 'react'
import './App.css'
import type { ApiStatus } from './app/api-status'
import { ApiStatusCard } from './components/ApiStatusCard'
import { checkApiHealth } from './services/health'

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')

  useEffect(() => {
    let isMounted = true

    checkApiHealth()
      .then(() => {
        if (isMounted) {
          setApiStatus('available')
        }
      })
      .catch(() => {
        if (isMounted) {
          setApiStatus('unavailable')
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="page-title">
        <p className="phase-label">Fase 2 · Fundación técnica</p>
        <h1 id="page-title">Agente Fitness</h1>
        <p className="hero__summary">
          La fundación técnica está en progreso. Esta pantalla confirma la
          comunicación mínima entre React y FastAPI.
        </p>
      </section>

      <ApiStatusCard status={apiStatus} />

      <p className="scope-note">
        Sin funciones de negocio: solo una base ejecutable y verificable.
      </p>
    </main>
  )
}

export default App
