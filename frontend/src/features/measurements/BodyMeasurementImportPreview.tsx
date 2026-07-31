import {
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from 'react'
import { ApiError } from '../../services/api'
import {
  previewBodyMeasurements,
  validateBodyMeasurementFile,
  type BodyMeasurementImportPreview as PreviewResult,
  type MeasurementCategory,
  type MeasurementPreview,
  type MeasurementSide,
  type MeasurementUnit,
} from '../../services/body-measurement-import'
import { useAuthentication } from '../auth/use-authentication'

type PreviewState = 'idle' | 'analyzing' | 'ready' | 'error'

const categoryLabels: Record<MeasurementCategory, string> = {
  bioimpedance: 'Bioimpedancia',
  skinfold: 'Pliegues',
  circumference: 'Perímetros',
}

const sideLabels: Record<MeasurementSide, string> = {
  none: 'Sin lado',
  left: 'Izquierdo',
  right: 'Derecho',
}

const unitLabels: Record<MeasurementUnit, string> = {
  kg: 'kg',
  cm: 'cm',
  mm: 'mm',
  percent: '%',
  kcal_per_day: 'kcal/día',
  years: 'años',
  unitless_index: 'índice',
  unitless_level: 'nivel',
}

function groupMetrics(
  metrics: MeasurementPreview[],
): Map<MeasurementCategory, MeasurementPreview[]> {
  const groups = new Map<
    MeasurementCategory,
    MeasurementPreview[]
  >()
  for (const metric of metrics) {
    const group = groups.get(metric.category) ?? []
    group.push(metric)
    groups.set(metric.category, group)
  }
  return groups
}

function previewErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'No se pudo conectar con la API. Revisa la conexión e inténtalo de nuevo.'
  }
  if ([401, 403].includes(error.status)) {
    return 'La sesión ha expirado. Inicia sesión de nuevo.'
  }
  if (error.status === 413) {
    return 'El archivo supera el límite permitido por el servidor.'
  }
  if (error.status === 415) {
    return 'El servidor no admite este formato. Usa un .xlsx sin macros.'
  }
  if (error.status === 422) {
    return 'El archivo no coincide con el formato de revisiones compatible.'
  }
  return 'No se pudo analizar el archivo. Inténtalo de nuevo.'
}

export function BodyMeasurementImportPreview() {
  const authentication = useAuthentication()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [state, setState] = useState<PreviewState>('idle')
  const [preview, setPreview] = useState<PreviewResult | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const groupedRevisions = useMemo(
    () =>
      preview?.revisions.map((revision, index) => ({
        revision,
        index,
        categories: groupMetrics(revision.metrics),
      })) ?? [],
    [preview],
  )

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] ?? null
    setPreview(null)
    setFile(null)
    setState('idle')
    setMessage(null)
    if (selectedFile === null) {
      return
    }
    const validation = validateBodyMeasurementFile(selectedFile)
    if (!validation.valid) {
      setState('error')
      setMessage(validation.message)
      event.target.value = ''
      return
    }
    setFile(selectedFile)
    setMessage('Archivo listo para analizar. Se mantiene solo en memoria.')
  }

  const analyze = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (file === null) {
      setState('error')
      setMessage('Selecciona un archivo .xlsx.')
      return
    }
    setState('analyzing')
    setMessage(null)
    setPreview(null)
    try {
      const result = await authentication.authenticatedRequest(
        previewBodyMeasurements(file),
      )
      setPreview(result)
      setState('ready')
    } catch (error) {
      setState('error')
      setMessage(previewErrorMessage(error))
    }
  }

  const changeFile = () => {
    setFile(null)
    setPreview(null)
    setState('idle')
    setMessage(null)
    if (inputRef.current !== null) {
      inputRef.current.value = ''
      inputRef.current.focus()
    }
  }

  return (
    <section
      className="measurements-card"
      aria-labelledby="measurements-title"
    >
      <p className="auth-card__eyebrow">Mediciones corporales</p>
      <h2 id="measurements-title">Previsualizar Excel</h2>
      <p className="auth-card__description">
        Analiza el formato V1 sin guardar el archivo ni las mediciones.
      </p>

      <form className="measurement-upload" onSubmit={analyze}>
        <div className="field">
          <label htmlFor="measurement-workbook">
            Archivo Excel <span>(.xlsx, máximo 5 MiB)</span>
          </label>
          <input
            ref={inputRef}
            id="measurement-workbook"
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={selectFile}
          />
        </div>
        <div className="form-actions">
          <button
            type="submit"
            disabled={file === null || state === 'analyzing'}
          >
            {state === 'analyzing'
              ? 'Analizando…'
              : 'Analizar archivo'}
          </button>
          {(file !== null || preview !== null) && (
            <button
              className="button-secondary"
              type="button"
              onClick={changeFile}
            >
              Seleccionar otro archivo
            </button>
          )}
        </div>
      </form>

      {state === 'analyzing' && (
        <p role="status" aria-live="polite">
          Analizando el archivo de forma segura…
        </p>
      )}
      {message && (
        <p
          className={state === 'error' ? 'auth-message' : 'form-note'}
          role={state === 'error' ? 'alert' : 'status'}
        >
          {message}
        </p>
      )}
      {state === 'error' && file !== null && (
        <button
          className="button-secondary"
          type="button"
          onClick={(event) => {
            const form = event.currentTarget.closest('section')?.querySelector(
              'form',
            )
            form?.requestSubmit()
          }}
        >
          Reintentar análisis
        </button>
      )}

      {state === 'ready' && preview && (
        <div className="measurement-preview">
          <div
            className={
              preview.totals.has_blocking_errors
                ? 'preview-summary preview-summary--blocked'
                : 'preview-summary'
            }
          >
            <h3>Resumen de la previsualización</h3>
            <p>
              {preview.totals.revision_count} revisiones ·{' '}
              {preview.totals.recognized_metric_values} valores reconocidos ·{' '}
              {preview.totals.unknown_metric_rows} métricas desconocidas
            </p>
            <p>
              {preview.totals.has_blocking_errors
                ? 'Hay ambigüedades bloqueantes. En esta entrega no se puede confirmar.'
                : 'La estructura se ha reconocido. En esta entrega no se puede confirmar.'}
            </p>
          </div>

          {preview.errors.length > 0 && (
            <section aria-labelledby="preview-errors-title">
              <h3 id="preview-errors-title">Errores bloqueantes</h3>
              <ul className="preview-issues preview-issues--errors">
                {preview.errors.map((issue, index) => (
                  <li key={`${issue.code}-${index}`}>{issue.message}</li>
                ))}
              </ul>
            </section>
          )}

          {preview.warnings.length > 0 && (
            <section aria-labelledby="preview-warnings-title">
              <h3 id="preview-warnings-title">Advertencias</h3>
              <ul className="preview-issues">
                {preview.warnings.map((issue, index) => (
                  <li key={`${issue.code}-${index}`}>{issue.message}</li>
                ))}
              </ul>
            </section>
          )}

          {preview.unknown_metrics.length > 0 && (
            <section aria-labelledby="unknown-metrics-title">
              <h3 id="unknown-metrics-title">Métricas desconocidas</h3>
              <ul className="preview-issues">
                {preview.unknown_metrics.map((metric) => (
                  <li key={`${metric.category_label}-${metric.original_label}`}>
                    {metric.original_label} · {metric.category_label}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <div className="revision-list">
            {groupedRevisions.map(({ revision, categories, index }) => (
              <article
                className="revision-card"
                key={`${revision.label}-${index}`}
              >
                <h3>Revisión {revision.label}</h3>
                {revision.date_status === 'missing_year' &&
                  revision.inferred_year !== null && (
                    <p className="form-note">
                      Año propuesto por contexto: {revision.inferred_year}{' '}
                      (sin resolver)
                    </p>
                  )}
                {[...categories.entries()].map(([category, metrics]) => (
                  <section
                    className="metric-group"
                    key={`${revision.label}-${category}`}
                  >
                    <h4>{categoryLabels[category]}</h4>
                    <dl className="metric-list">
                      {metrics.map((metric, metricIndex) => (
                        <div
                          key={`${metric.code}-${metric.side}-${metricIndex}`}
                          className="metric-list__item"
                        >
                          <dt>{metric.original_label}</dt>
                          <dd>
                            {sideLabels[metric.side]} · {metric.value}{' '}
                            {metric.unit
                              ? unitLabels[metric.unit]
                              : 'unidad pendiente'}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </section>
                ))}
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
