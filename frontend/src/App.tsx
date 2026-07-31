import { useEffect, useState } from 'react'
import './App.css'
import type { ApiStatus } from './app/api-status'
import { ApiStatusCard } from './components/ApiStatusCard'
import { LoginForm } from './features/auth/LoginForm'
import { useAuthentication } from './features/auth/use-authentication'
import { BodyMeasurementImportPreview } from './features/measurements/BodyMeasurementImportPreview'
import { ProfileSection } from './features/profile/ProfileSection'
import { checkApiHealth } from './services/health'

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')
  const authentication = useAuthentication()

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
        <p className="phase-label">Fase 3 · Autenticación y perfil</p>
        <h1 id="page-title">Agente Fitness</h1>
        <p className="hero__summary">
          Gestión de sesión segura sobre la fundación React, FastAPI y
          PostgreSQL.
        </p>
      </section>

      <div className="content-grid">
        <ApiStatusCard status={apiStatus} />

        <section className="auth-card" aria-labelledby="session-title">
          <p className="auth-card__eyebrow">Cuenta</p>
          <h2 id="session-title">
            {authentication.status === 'authenticated'
              ? 'Sesión activa'
              : 'Acceso'}
          </h2>

          {authentication.status === 'loading' && (
            <p role="status" aria-live="polite">
              Comprobando sesión…
            </p>
          )}

          {authentication.message && (
            <p className="auth-message" role="alert">
              {authentication.message}
            </p>
          )}

          {authentication.status === 'anonymous' && (
            <>
              <p className="auth-card__description">
                Inicia sesión con una cuenta ya registrada.
              </p>
              <LoginForm
                isSubmitting={authentication.isSubmitting}
                onSubmit={authentication.login}
              />
            </>
          )}

          {authentication.status === 'authenticated' &&
            authentication.user && (
              <div className="session-summary">
                <p className="session-summary__label">
                  Usuario autenticado
                </p>
                <p className="session-summary__email">
                  {authentication.user.email}
                </p>
                <button
                  className="button-secondary"
                  type="button"
                  disabled={authentication.isSubmitting}
                  onClick={() => void authentication.logout()}
                >
                  {authentication.isSubmitting
                    ? 'Cerrando sesión…'
                    : 'Cerrar sesión'}
                </button>
              </div>
            )}
        </section>

        {authentication.status === 'authenticated' && (
          <ProfileSection />
        )}

        {authentication.status === 'authenticated' && (
          <BodyMeasurementImportPreview />
        )}
      </div>

      <p className="scope-note">
        El access token se conserva solo en memoria; la cookie de renovación
        no es accesible desde JavaScript. El perfil y la previsualización son
        privados y se consultan mediante el access token.
      </p>
    </main>
  )
}

export default App
