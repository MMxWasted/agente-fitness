import { useState, type FormEvent } from 'react'
import type {
  ExperienceLevel,
  FitnessProfile,
  ProfileInput,
  UnitSystem,
} from '../../services/profile'

interface ProfileFormProps {
  profile: FitnessProfile | null
  isSaving: boolean
  onCancel?: () => void
  onSave: (profile: ProfileInput) => Promise<void>
}

type FieldErrors = Partial<
  Record<
    | 'displayName'
    | 'birthDate'
    | 'height'
    | 'experienceLevel'
    | 'timezone'
    | 'unitSystem',
    string
  >
>

const commonTimezones = [
  'UTC',
  'Europe/Madrid',
  'Europe/London',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Mexico_City',
  'America/Bogota',
  'America/Argentina/Buenos_Aires',
  'Asia/Tokyo',
  'Australia/Sydney',
]

function formatEditableHeight(
  heightCm: number | null,
  unitSystem: UnitSystem | '',
): string {
  if (heightCm === null) {
    return ''
  }
  const value = unitSystem === 'imperial' ? heightCm / 2.54 : heightCm
  return String(Number(value.toFixed(2)))
}

function toHeightCm(
  height: string,
  unitSystem: UnitSystem | '',
): number | null {
  if (height.trim() === '') {
    return null
  }
  const parsedHeight = Number(height)
  if (!Number.isFinite(parsedHeight)) {
    return Number.NaN
  }
  const heightCm =
    unitSystem === 'imperial' ? parsedHeight * 2.54 : parsedHeight
  return Number(heightCm.toFixed(2))
}

export function ProfileForm({
  profile,
  isSaving,
  onCancel,
  onSave,
}: ProfileFormProps) {
  const [displayName, setDisplayName] = useState(
    profile?.display_name ?? '',
  )
  const [birthDate, setBirthDate] = useState(
    profile?.birth_date ?? '',
  )
  const [experienceLevel, setExperienceLevel] = useState<
    ExperienceLevel | ''
  >(profile?.experience_level ?? '')
  const [timezone, setTimezone] = useState(profile?.timezone ?? '')
  const [unitSystem, setUnitSystem] = useState<UnitSystem | ''>(
    profile?.unit_system ?? '',
  )
  const [height, setHeight] = useState(
    formatEditableHeight(
      profile?.height_cm ?? null,
      profile?.unit_system ?? '',
    ),
  )
  const [errors, setErrors] = useState<FieldErrors>({})

  const changeUnitSystem = (nextUnitSystem: UnitSystem | '') => {
    const currentHeightCm = toHeightCm(height, unitSystem)
    setUnitSystem(nextUnitSystem)
    setHeight(
      Number.isFinite(currentHeightCm)
        ? formatEditableHeight(currentHeightCm, nextUnitSystem)
        : '',
    )
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextErrors: FieldErrors = {}
    const normalizedDisplayName = displayName.trim()
    const normalizedTimezone = timezone.trim()
    const heightCm = toHeightCm(height, unitSystem)

    if (
      normalizedDisplayName.length === 0 ||
      normalizedDisplayName.length > 80
    ) {
      nextErrors.displayName =
        'El nombre visible debe tener entre 1 y 80 caracteres.'
    }
    if (
      birthDate !== '' &&
      birthDate > new Date().toISOString().slice(0, 10)
    ) {
      nextErrors.birthDate =
        'La fecha de nacimiento no puede estar en el futuro.'
    }
    if (
      heightCm !== null &&
      (!Number.isFinite(heightCm) || heightCm <= 0 || heightCm > 300)
    ) {
      nextErrors.height =
        'La altura debe ser mayor que 0 y como máximo 300 cm.'
    }
    if (experienceLevel === '') {
      nextErrors.experienceLevel =
        'Selecciona un nivel de experiencia.'
    }
    if (normalizedTimezone.length === 0) {
      nextErrors.timezone = 'Indica una zona horaria IANA.'
    }
    if (unitSystem === '') {
      nextErrors.unitSystem = 'Selecciona un sistema de unidades.'
    }

    setErrors(nextErrors)
    if (
      Object.keys(nextErrors).length > 0 ||
      experienceLevel === '' ||
      unitSystem === ''
    ) {
      return
    }

    void onSave({
      display_name: normalizedDisplayName,
      birth_date: birthDate || null,
      height_cm: heightCm,
      experience_level: experienceLevel,
      timezone: normalizedTimezone,
      unit_system: unitSystem,
    })
  }

  const heightLabel =
    unitSystem === 'imperial' ? 'Altura (pulgadas)' : 'Altura (cm)'

  return (
    <form className="profile-form" onSubmit={handleSubmit} noValidate>
      <div className="field">
        <label htmlFor="profile-display-name">Nombre visible</label>
        <input
          id="profile-display-name"
          name="display_name"
          required
          maxLength={80}
          value={displayName}
          aria-invalid={Boolean(errors.displayName)}
          aria-describedby={
            errors.displayName ? 'profile-display-name-error' : undefined
          }
          onChange={(event) =>
            setDisplayName(event.currentTarget.value)
          }
        />
        {errors.displayName && (
          <p
            id="profile-display-name-error"
            className="field-error"
          >
            {errors.displayName}
          </p>
        )}
      </div>

      <div className="profile-form__row">
        <div className="field">
          <label htmlFor="profile-birth-date">
            Fecha de nacimiento <span>(opcional)</span>
          </label>
          <input
            id="profile-birth-date"
            name="birth_date"
            type="date"
            value={birthDate}
            aria-invalid={Boolean(errors.birthDate)}
            aria-describedby={
              errors.birthDate ? 'profile-birth-date-error' : undefined
            }
            onChange={(event) =>
              setBirthDate(event.currentTarget.value)
            }
          />
          {errors.birthDate && (
            <p
              id="profile-birth-date-error"
              className="field-error"
            >
              {errors.birthDate}
            </p>
          )}
        </div>

        <div className="field">
          <label htmlFor="profile-experience">
            Nivel de experiencia
          </label>
          <select
            id="profile-experience"
            name="experience_level"
            required
            value={experienceLevel}
            aria-invalid={Boolean(errors.experienceLevel)}
            aria-describedby={
              errors.experienceLevel
                ? 'profile-experience-error'
                : undefined
            }
            onChange={(event) =>
              setExperienceLevel(
                event.currentTarget.value as ExperienceLevel | '',
              )
            }
          >
            <option value="">Selecciona una opción</option>
            <option value="beginner">Principiante</option>
            <option value="intermediate">Intermedio</option>
            <option value="advanced">Avanzado</option>
          </select>
          {errors.experienceLevel && (
            <p
              id="profile-experience-error"
              className="field-error"
            >
              {errors.experienceLevel}
            </p>
          )}
        </div>
      </div>

      <div className="profile-form__row">
        <div className="field">
          <label htmlFor="profile-unit-system">
            Sistema de unidades
          </label>
          <select
            id="profile-unit-system"
            name="unit_system"
            required
            value={unitSystem}
            aria-invalid={Boolean(errors.unitSystem)}
            aria-describedby={
              errors.unitSystem
                ? 'profile-unit-system-error'
                : undefined
            }
            onChange={(event) =>
              changeUnitSystem(
                event.currentTarget.value as UnitSystem | '',
              )
            }
          >
            <option value="">Selecciona una opción</option>
            <option value="metric">Métrico</option>
            <option value="imperial">Imperial</option>
          </select>
          {errors.unitSystem && (
            <p
              id="profile-unit-system-error"
              className="field-error"
            >
              {errors.unitSystem}
            </p>
          )}
        </div>

        <div className="field">
          <label htmlFor="profile-height">
            {heightLabel} <span>(opcional)</span>
          </label>
          <input
            id="profile-height"
            name="height"
            type="number"
            inputMode="decimal"
            min="0.01"
            max={unitSystem === 'imperial' ? '118.11' : '300'}
            step="0.01"
            value={height}
            aria-invalid={Boolean(errors.height)}
            aria-describedby={
              errors.height ? 'profile-height-error' : undefined
            }
            onChange={(event) =>
              setHeight(event.currentTarget.value)
            }
          />
          {errors.height && (
            <p id="profile-height-error" className="field-error">
              {errors.height}
            </p>
          )}
        </div>
      </div>

      <div className="field">
        <label htmlFor="profile-timezone">Zona horaria IANA</label>
        <input
          id="profile-timezone"
          name="timezone"
          list="profile-timezone-options"
          required
          maxLength={64}
          placeholder="Europe/Madrid"
          value={timezone}
          aria-invalid={Boolean(errors.timezone)}
          aria-describedby={
            errors.timezone ? 'profile-timezone-error' : undefined
          }
          onChange={(event) => setTimezone(event.currentTarget.value)}
        />
        <datalist id="profile-timezone-options">
          {commonTimezones.map((candidate) => (
            <option key={candidate} value={candidate} />
          ))}
        </datalist>
        {errors.timezone && (
          <p id="profile-timezone-error" className="field-error">
            {errors.timezone}
          </p>
        )}
      </div>

      <p className="form-note">
        La fecha y la altura son opcionales. La altura se guarda
        internamente en centímetros.
      </p>

      <div className="form-actions">
        <button type="submit" disabled={isSaving}>
          {isSaving ? 'Guardando…' : 'Guardar perfil'}
        </button>
        {onCancel && (
          <button
            className="button-secondary"
            type="button"
            disabled={isSaving}
            onClick={onCancel}
          >
            Cancelar
          </button>
        )}
      </div>
    </form>
  )
}
