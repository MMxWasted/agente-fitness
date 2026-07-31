import { useCallback, useEffect, useState } from 'react'
import { ApiError } from '../../services/api'
import {
  getProfile,
  putProfile,
  type FitnessProfile,
  type ProfileInput,
} from '../../services/profile'
import { useAuthentication } from '../auth/use-authentication'
import { ProfileForm } from './ProfileForm'

type ProfileState = 'loading' | 'missing' | 'ready' | 'error'

const experienceLabels = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
} as const

function formatHeight(profile: FitnessProfile): string {
  if (profile.height_cm === null) {
    return 'No indicada'
  }
  if (profile.unit_system === 'metric') {
    return `${profile.height_cm} cm`
  }

  const totalInches = profile.height_cm / 2.54
  const feet = Math.floor(totalInches / 12)
  const inches = totalInches - feet * 12
  return `${feet} ft ${Number(inches.toFixed(1))} in`
}

export function ProfileSection() {
  const authentication = useAuthentication()
  const [state, setState] = useState<ProfileState>('loading')
  const [profile, setProfile] = useState<FitnessProfile | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const loadProfile = useCallback(async () => {
    setState('loading')
    setMessage(null)
    try {
      const loadedProfile =
        await authentication.authenticatedRequest(getProfile)
      setProfile(loadedProfile)
      setState('ready')
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        setProfile(null)
        setState('missing')
        return
      }
      setState('error')
      setMessage(
        error instanceof ApiError &&
          [401, 403].includes(error.status)
          ? 'La sesión ha expirado. Inicia sesión de nuevo.'
          : 'No se pudo cargar el perfil. Revisa la conexión e inténtalo de nuevo.',
      )
    }
  }, [authentication])

  useEffect(() => {
    void loadProfile()
  }, [loadProfile])

  const saveProfile = async (profileInput: ProfileInput) => {
    setIsSaving(true)
    setMessage(null)
    try {
      const savedProfile = await authentication.authenticatedRequest(
        putProfile(profileInput),
      )
      setProfile(savedProfile)
      setState('ready')
      setIsEditing(false)
      setMessage('Perfil guardado correctamente.')
    } catch (error) {
      if (
        error instanceof ApiError &&
        [401, 403].includes(error.status)
      ) {
        setMessage('La sesión ha expirado. Inicia sesión de nuevo.')
      } else if (error instanceof ApiError && error.status === 422) {
        setMessage(
          'El servidor rechazó algún valor. Revisa los campos del perfil.',
        )
      } else {
        setMessage(
          'No se pudo guardar el perfil. Revisa la conexión e inténtalo de nuevo.',
        )
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="profile-card" aria-labelledby="profile-title">
      <p className="auth-card__eyebrow">Perfil privado</p>
      <h2 id="profile-title">Perfil fitness básico</h2>

      {state === 'loading' && (
        <p role="status" aria-live="polite">
          Cargando perfil…
        </p>
      )}

      {message && (
        <p
          className={
            state === 'ready'
              ? 'success-message'
              : 'auth-message'
          }
          role={state === 'ready' ? 'status' : 'alert'}
        >
          {message}
        </p>
      )}

      {state === 'error' && (
        <button
          className="button-secondary"
          type="button"
          onClick={() => void loadProfile()}
        >
          Reintentar
        </button>
      )}

      {state === 'missing' && (
        <>
          <p className="auth-card__description">
            Todavía no tienes perfil. Añade únicamente tu contexto
            básico para continuar.
          </p>
          <ProfileForm
            profile={null}
            isSaving={isSaving}
            onSave={saveProfile}
          />
        </>
      )}

      {state === 'ready' && profile && !isEditing && (
        <>
          <dl className="profile-summary">
            <div>
              <dt>Nombre visible</dt>
              <dd>{profile.display_name}</dd>
            </div>
            <div>
              <dt>Experiencia</dt>
              <dd>{experienceLabels[profile.experience_level]}</dd>
            </div>
            <div>
              <dt>Fecha de nacimiento</dt>
              <dd>{profile.birth_date ?? 'No indicada'}</dd>
            </div>
            <div>
              <dt>Altura</dt>
              <dd>{formatHeight(profile)}</dd>
            </div>
            <div>
              <dt>Zona horaria</dt>
              <dd>{profile.timezone}</dd>
            </div>
            <div>
              <dt>Unidades</dt>
              <dd>
                {profile.unit_system === 'metric'
                  ? 'Métrico'
                  : 'Imperial'}
              </dd>
            </div>
          </dl>
          <button
            className="button-secondary"
            type="button"
            onClick={() => {
              setMessage(null)
              setIsEditing(true)
            }}
          >
            Editar perfil
          </button>
        </>
      )}

      {state === 'ready' && profile && isEditing && (
        <ProfileForm
          key={profile.updated_at}
          profile={profile}
          isSaving={isSaving}
          onSave={saveProfile}
          onCancel={() => setIsEditing(false)}
        />
      )}
    </section>
  )
}
