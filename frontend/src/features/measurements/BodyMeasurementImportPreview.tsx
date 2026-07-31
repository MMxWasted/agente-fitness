import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from 'react'
import { ApiError } from '../../services/api'
import {
  confirmBodyMeasurementImport,
  createBodyMeasurementSource,
  emptyImportDecisions,
  getBodyMeasurementReview,
  listBodyMeasurementImports,
  listBodyMeasurementReviews,
  listBodyMeasurementSources,
  planBodyMeasurementImport,
  revertBodyMeasurementImport,
  type BodyMeasurementImportDecisions,
  type BodyMeasurementImportPlan,
  type BodyMeasurementImportRecord,
  type BodyMeasurementReview,
  type BodyMeasurementReviewDetail,
  type BodyMeasurementSource,
} from '../../services/body-measurement-history'
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
type HistoryState = 'loading' | 'ready' | 'error'
const historyPageSize = 5

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

const classificationLabels = {
  new: 'Nueva',
  identical: 'Idéntica',
  modified: 'Modificada',
  blocked: 'Bloqueada',
  excluded: 'Excluida',
} as const

function groupMetrics(
  metrics: MeasurementPreview[],
): Map<MeasurementCategory, MeasurementPreview[]> {
  const groups = new Map<MeasurementCategory, MeasurementPreview[]>()
  for (const metric of metrics) {
    const group = groups.get(metric.category) ?? []
    group.push(metric)
    groups.set(metric.category, group)
  }
  return groups
}

function operationErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'No se pudo conectar con la API. Revisa la conexión e inténtalo de nuevo.'
  }
  if ([401, 403].includes(error.status)) {
    return 'La sesión ha expirado. Inicia sesión de nuevo.'
  }
  if (error.status === 409) {
    return 'El historial cambió o la operación entra en conflicto. Actualiza y vuelve a planificar.'
  }
  if (error.status === 413) {
    return 'El archivo supera el límite permitido por el servidor.'
  }
  if (error.status === 415) {
    return 'El servidor no admite este formato. Usa un .xlsx sin macros.'
  }
  if (error.status === 422) {
    return 'Hay decisiones pendientes o el archivo no coincide con el formato compatible.'
  }
  return 'La operación no se pudo completar. Inténtalo de nuevo.'
}

function newIdempotencyKey(): string {
  return `body-measurement-${crypto.randomUUID()}`
}

export function BodyMeasurementImportPreview() {
  const authentication = useAuthentication()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [state, setState] = useState<PreviewState>('idle')
  const [preview, setPreview] = useState<PreviewResult | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [historyState, setHistoryState] = useState<HistoryState>('loading')
  const [sources, setSources] = useState<BodyMeasurementSource[]>([])
  const [imports, setImports] = useState<BodyMeasurementImportRecord[]>([])
  const [reviews, setReviews] = useState<BodyMeasurementReview[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState('')
  const [sourceName, setSourceName] = useState('')
  const [sourceKey, setSourceKey] = useState('')
  const [isCreatingSource, setIsCreatingSource] = useState(false)
  const [decisions, setDecisions] = useState<BodyMeasurementImportDecisions>(
    emptyImportDecisions,
  )
  const [plan, setPlan] = useState<BodyMeasurementImportPlan | null>(null)
  const [isPlanning, setIsPlanning] = useState(false)
  const [isConfirming, setIsConfirming] = useState(false)
  const [confirmationAccepted, setConfirmationAccepted] = useState(false)
  const [idempotencyKey, setIdempotencyKey] = useState<string | null>(null)
  const [lastImport, setLastImport] =
    useState<BodyMeasurementImportRecord | null>(null)
  const [reviewDetail, setReviewDetail] =
    useState<BodyMeasurementReviewDetail | null>(null)
  const [detailLoadingId, setDetailLoadingId] = useState<string | null>(null)
  const [revertingId, setRevertingId] = useState<string | null>(null)
  const [reviewPageIndex, setReviewPageIndex] = useState(0)
  const [importPageIndex, setImportPageIndex] = useState(0)

  const groupedRevisions = useMemo(
    () =>
      preview?.revisions.map((revision, index) => ({
        revision,
        index,
        categories: groupMetrics(revision.metrics),
      })) ?? [],
    [preview],
  )

  const displayedImports = selectedSourceId
    ? imports.filter((item) => item.source_id === selectedSourceId)
    : imports
  const displayedReviews = selectedSourceId
    ? reviews.filter((item) => item.source_id === selectedSourceId)
    : reviews
  const pagedImports = displayedImports.slice(
    importPageIndex * historyPageSize,
    (importPageIndex + 1) * historyPageSize,
  )
  const pagedReviews = displayedReviews.slice(
    reviewPageIndex * historyPageSize,
    (reviewPageIndex + 1) * historyPageSize,
  )

  const loadHistory = useCallback(async () => {
    setHistoryState('loading')
    try {
      const [sourcePage, importPage, reviewPage] = await Promise.all([
        authentication.authenticatedRequest(listBodyMeasurementSources),
        authentication.authenticatedRequest(listBodyMeasurementImports),
        authentication.authenticatedRequest(listBodyMeasurementReviews),
      ])
      setSources(sourcePage.items)
      setImports(importPage.items)
      setReviews(reviewPage.items)
      setSelectedSourceId((current) => current || sourcePage.items[0]?.id || '')
      setImportPageIndex(0)
      setReviewPageIndex(0)
      setHistoryState('ready')
    } catch (error) {
      setHistoryState('error')
      setMessage(operationErrorMessage(error))
    }
  }, [authentication])

  useEffect(() => {
    void loadHistory()
  }, [loadHistory])

  const resetPlan = () => {
    setPlan(null)
    setConfirmationAccepted(false)
    setIdempotencyKey(null)
    setLastImport(null)
  }

  const updateDecisions = (
    updater: (current: BodyMeasurementImportDecisions) => BodyMeasurementImportDecisions,
  ) => {
    setDecisions(updater)
    resetPlan()
  }

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] ?? null
    setPreview(null)
    setFile(null)
    setState('idle')
    setMessage(null)
    setDecisions(emptyImportDecisions())
    resetPlan()
    if (selectedFile === null) return
    const validation = validateBodyMeasurementFile(selectedFile)
    if (!validation.valid) {
      setState('error')
      setMessage(validation.message)
      event.target.value = ''
      return
    }
    setFile(selectedFile)
    setMessage('Archivo listo. Se conserva únicamente en memoria.')
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
    resetPlan()
    try {
      const result = await authentication.authenticatedRequest(
        previewBodyMeasurements(file),
      )
      setPreview(result)
      setState('ready')
    } catch (error) {
      setState('error')
      setMessage(operationErrorMessage(error))
    }
  }

  const createSource = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!sourceName.trim() || !sourceKey.trim()) return
    setIsCreatingSource(true)
    setMessage(null)
    try {
      const source = await authentication.authenticatedRequest(
        createBodyMeasurementSource(sourceName.trim(), sourceKey.trim()),
      )
      setSources((current) => [...current, source])
      setSelectedSourceId(source.id)
      setSourceName('')
      setSourceKey('')
      setMessage('Fuente creada correctamente.')
    } catch (error) {
      setMessage(operationErrorMessage(error))
    } finally {
      setIsCreatingSource(false)
    }
  }

  const planImport = async () => {
    if (file === null || preview === null || !selectedSourceId) return
    setIsPlanning(true)
    setMessage(null)
    resetPlan()
    try {
      const result = await authentication.authenticatedRequest(
        planBodyMeasurementImport(
          file,
          selectedSourceId,
          preview,
          decisions,
        ),
      )
      setPlan(result)
      setMessage('Plan calculado. Revisa el resumen antes de confirmar.')
    } catch (error) {
      setMessage(operationErrorMessage(error))
    } finally {
      setIsPlanning(false)
    }
  }

  const confirmImport = async () => {
    if (
      file === null ||
      preview === null ||
      plan === null ||
      !selectedSourceId ||
      !confirmationAccepted
    ) {
      return
    }
    const key = idempotencyKey ?? newIdempotencyKey()
    setIdempotencyKey(key)
    setIsConfirming(true)
    setMessage(null)
    try {
      const result = await authentication.authenticatedRequest(
        confirmBodyMeasurementImport(
          file,
          selectedSourceId,
          preview,
          plan,
          decisions,
          key,
        ),
      )
      setLastImport(result)
      setConfirmationAccepted(false)
      setIdempotencyKey(null)
      setMessage('Importación confirmada y registrada.')
      await loadHistory()
    } catch (error) {
      setMessage(operationErrorMessage(error))
    } finally {
      setIsConfirming(false)
    }
  }

  const openReview = async (reviewId: string) => {
    setDetailLoadingId(reviewId)
    setMessage(null)
    try {
      const detail = await authentication.authenticatedRequest(
        getBodyMeasurementReview(reviewId),
      )
      setReviewDetail(detail)
    } catch (error) {
      setMessage(operationErrorMessage(error))
    } finally {
      setDetailLoadingId(null)
    }
  }

  const revertImport = async (item: BodyMeasurementImportRecord) => {
    if (
      !window.confirm(
        '¿Revertir esta importación? El historial se restaurará de forma transaccional.',
      )
    ) {
      return
    }
    setRevertingId(item.id)
    setMessage(null)
    try {
      await authentication.authenticatedRequest(
        revertBodyMeasurementImport(item.id),
      )
      setMessage('Importación revertida correctamente.')
      setReviewDetail(null)
      await loadHistory()
    } catch (error) {
      setMessage(operationErrorMessage(error))
    } finally {
      setRevertingId(null)
    }
  }

  const changeFile = () => {
    setFile(null)
    setPreview(null)
    setState('idle')
    setMessage(null)
    setDecisions(emptyImportDecisions())
    resetPlan()
    if (inputRef.current !== null) {
      inputRef.current.value = ''
      inputRef.current.focus()
    }
  }

  const setRevisionExcluded = (revisionIndex: number, checked: boolean) => {
    updateDecisions((current) => ({
      ...current,
      excluded_revisions: checked
        ? [...current.excluded_revisions, revisionIndex]
        : current.excluded_revisions.filter((item) => item !== revisionIndex),
    }))
  }

  const setDateResolution = (revisionIndex: number, value: string) => {
    updateDecisions((current) => ({
      ...current,
      date_resolutions: [
        ...current.date_resolutions.filter(
          (item) => item.revision_index !== revisionIndex,
        ),
        ...(value ? [{ revision_index: revisionIndex, measurement_date: value }] : []),
      ],
    }))
  }

  const setDisambiguator = (revisionIndex: number, value: string) => {
    updateDecisions((current) => ({
      ...current,
      disambiguators: [
        ...current.disambiguators.filter(
          (item) => item.revision_index !== revisionIndex,
        ),
        ...(value.trim()
          ? [{ revision_index: revisionIndex, disambiguator: value }]
          : []),
      ],
    }))
  }

  const setMetricExcluded = (
    revisionIndex: number,
    metric: MeasurementPreview,
    checked: boolean,
  ) => {
    updateDecisions((current) => ({
      ...current,
      excluded_metrics: checked
        ? [
            ...current.excluded_metrics,
            {
              revision_index: revisionIndex,
              metric_code: metric.code,
              side: metric.side,
            },
          ]
        : current.excluded_metrics.filter(
            (item) =>
              item.revision_index !== revisionIndex ||
              item.metric_code !== metric.code ||
              item.side !== metric.side,
          ),
    }))
  }

  const setUnitAccepted = (metric: MeasurementPreview, checked: boolean) => {
    updateDecisions((current) => ({
      ...current,
      unit_resolutions: checked
        ? [
            ...current.unit_resolutions.filter(
              (item) =>
                item.metric_code !== metric.code || item.side !== metric.side,
            ),
            {
              metric_code: metric.code,
              side: metric.side,
              action: 'accept_canonical',
            },
          ]
        : current.unit_resolutions.filter(
            (item) =>
              item.metric_code !== metric.code || item.side !== metric.side,
          ),
    }))
  }

  const setUnknownExcluded = (
    unknown: PreviewResult['unknown_metrics'][number],
    checked: boolean,
  ) => {
    updateDecisions((current) => ({
      ...current,
      excluded_unknown_metrics: checked
        ? [
            ...current.excluded_unknown_metrics,
            {
              category_label: unknown.category_label,
              original_label: unknown.original_label,
              side: unknown.side,
            },
          ]
        : current.excluded_unknown_metrics.filter(
            (item) =>
              item.category_label !== unknown.category_label ||
              item.original_label !== unknown.original_label ||
              item.side !== unknown.side,
          ),
    }))
  }

  const setModificationAccepted = (revisionIndex: number, checked: boolean) => {
    setDecisions((current) => ({
      ...current,
      modifications: [
        ...current.modifications.filter(
          (item) => item.revision_index !== revisionIndex,
        ),
        ...(checked
          ? [{ revision_index: revisionIndex, action: 'create_version' as const }]
          : []),
      ],
    }))
    setConfirmationAccepted(false)
    setIdempotencyKey(null)
  }

  const hasUnacceptedModifications =
    plan?.revisions.some(
      (revision) =>
        revision.classification === 'modified' &&
        !decisions.modifications.some(
          (decision) =>
            decision.revision_index === revision.revision_index &&
            decision.action === 'create_version',
        ),
    ) ?? false

  return (
    <section className="measurements-card" aria-labelledby="measurements-title">
      <p className="auth-card__eyebrow">Mediciones corporales privadas</p>
      <h2 id="measurements-title">Importar e historial</h2>
      <p className="auth-card__description">
        Previsualiza, resuelve ambigüedades y confirma un Excel V1. El archivo y
        la clave de idempotencia se mantienen solo en memoria.
      </p>

      {message && (
        <p className={message.includes('correctamente') || message.includes('calculado') ? 'success-message' : 'auth-message'} role={message.includes('correctamente') || message.includes('calculado') ? 'status' : 'alert'}>
          {message}
        </p>
      )}

      <section className="measurement-section" aria-labelledby="source-title">
        <h3 id="source-title">1. Fuente lógica</h3>
        <div className="field">
          <label htmlFor="measurement-source">Fuente del historial</label>
          <select
            id="measurement-source"
            value={selectedSourceId}
            onChange={(event) => {
              setSelectedSourceId(event.target.value)
              setImportPageIndex(0)
              setReviewPageIndex(0)
              setReviewDetail(null)
              resetPlan()
            }}
          >
            <option value="">Selecciona una fuente</option>
            {sources.map((source) => (
              <option key={source.id} value={source.id}>
                {source.display_name}
              </option>
            ))}
          </select>
        </div>
        <form className="source-form" onSubmit={createSource}>
          <div className="field">
            <label htmlFor="source-display-name">Nombre de nueva fuente</label>
            <input id="source-display-name" value={sourceName} maxLength={80} onChange={(event) => setSourceName(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="source-logical-key">Clave lógica</label>
            <input id="source-logical-key" value={sourceKey} maxLength={64} pattern="[a-z0-9][a-z0-9._-]*" onChange={(event) => setSourceKey(event.target.value.toLowerCase())} />
          </div>
          <button type="submit" disabled={isCreatingSource || !sourceName.trim() || !sourceKey.trim()}>
            {isCreatingSource ? 'Creando…' : 'Crear fuente'}
          </button>
        </form>
      </section>

      <section className="measurement-section" aria-labelledby="file-title">
        <h3 id="file-title">2. Previsualización</h3>
        <form className="measurement-upload" onSubmit={analyze}>
          <div className="field">
            <label htmlFor="measurement-workbook">Archivo Excel <span>(.xlsx, máximo 5 MiB)</span></label>
            <input ref={inputRef} id="measurement-workbook" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={selectFile} />
          </div>
          <div className="form-actions">
            <button type="submit" disabled={file === null || state === 'analyzing'}>
              {state === 'analyzing' ? 'Analizando…' : 'Analizar archivo'}
            </button>
            {(file !== null || preview !== null) && <button className="button-secondary" type="button" onClick={changeFile}>Seleccionar otro archivo</button>}
          </div>
        </form>
        {state === 'analyzing' && <p role="status">Analizando el archivo de forma segura…</p>}
        {state === 'error' && file !== null && <button className="button-secondary" type="button" onClick={() => inputRef.current?.form?.requestSubmit()}>Reintentar análisis</button>}
      </section>

      {state === 'ready' && preview && (
        <div className="measurement-preview">
          <div className={preview.totals.has_blocking_errors ? 'preview-summary preview-summary--blocked' : 'preview-summary'}>
            <h3>Resumen de la previsualización</h3>
            <p>{preview.totals.revision_count} revisiones · {preview.totals.recognized_metric_values} valores reconocidos · {preview.totals.unknown_metric_rows} métricas desconocidas</p>
            <p>Las ambigüedades deben resolverse o excluirse explícitamente antes de confirmar.</p>
          </div>

          {preview.errors.length > 0 && <section aria-labelledby="preview-errors-title"><h3 id="preview-errors-title">Errores bloqueantes</h3><ul className="preview-issues preview-issues--errors">{preview.errors.map((issue, index) => <li key={`${issue.code}-${index}`}>{issue.message}</li>)}</ul></section>}
          {preview.warnings.length > 0 && <section aria-labelledby="preview-warnings-title"><h3 id="preview-warnings-title">Advertencias</h3><ul className="preview-issues">{preview.warnings.map((issue, index) => <li key={`${issue.code}-${index}`}>{issue.message}</li>)}</ul></section>}

          {preview.unknown_metrics.length > 0 && (
            <fieldset className="decision-fieldset">
              <legend>Métricas desconocidas</legend>
              {preview.unknown_metrics.map((unknown) => (
                <label key={`${unknown.category_label}-${unknown.original_label}-${unknown.side}`}>
                  <input type="checkbox" checked={decisions.excluded_unknown_metrics.some((item) => item.category_label === unknown.category_label && item.original_label === unknown.original_label && item.side === unknown.side)} onChange={(event) => setUnknownExcluded(unknown, event.target.checked)} />
                  Excluir {unknown.original_label} · {unknown.category_label}
                </label>
              ))}
            </fieldset>
          )}

          <div className="revision-list">
            {groupedRevisions.map(({ revision, categories, index }) => (
              <article className="revision-card" key={`${revision.label}-${index}`}>
                <h3>Revisión {revision.label}</h3>
                <label className="decision-option"><input type="checkbox" checked={decisions.excluded_revisions.includes(index)} onChange={(event) => setRevisionExcluded(index, event.target.checked)} />Excluir revisión completa</label>
                {revision.date_status === 'missing_year' && <div className="field"><label htmlFor={`resolved-date-${index}`}>Fecha completa obligatoria</label><input id={`resolved-date-${index}`} type="date" max={new Date().toISOString().slice(0, 10)} value={decisions.date_resolutions.find((item) => item.revision_index === index)?.measurement_date ?? ''} onChange={(event) => setDateResolution(index, event.target.value)} /></div>}
                <div className="field"><label htmlFor={`disambiguator-${index}`}>Desambiguador opcional</label><input id={`disambiguator-${index}`} maxLength={64} value={decisions.disambiguators.find((item) => item.revision_index === index)?.disambiguator ?? ''} onChange={(event) => setDisambiguator(index, event.target.value)} /></div>
                {[...categories.entries()].map(([category, metrics]) => (
                  <section className="metric-group" key={`${revision.label}-${category}`}>
                    <h4>{categoryLabels[category]}</h4>
                    <dl className="metric-list">
                      {metrics.map((metric, metricIndex) => (
                        <div key={`${metric.code}-${metric.side}-${metricIndex}`} className="metric-list__item">
                          <dt>{metric.original_label}</dt><dd>{sideLabels[metric.side]} · {metric.value} {metric.unit ? unitLabels[metric.unit] : 'unidad pendiente'}</dd>
                          {metric.unit === null && <label className="decision-option"><input type="checkbox" checked={decisions.unit_resolutions.some((item) => item.metric_code === metric.code && item.side === metric.side)} onChange={(event) => setUnitAccepted(metric, event.target.checked)} />Aceptar unidad canónica</label>}
                          <label className="decision-option"><input type="checkbox" checked={decisions.excluded_metrics.some((item) => item.revision_index === index && item.metric_code === metric.code && item.side === metric.side)} onChange={(event) => setMetricExcluded(index, metric, event.target.checked)} />Excluir valor</label>
                        </div>
                      ))}
                    </dl>
                  </section>
                ))}
              </article>
            ))}
          </div>

          <button type="button" disabled={!selectedSourceId || isPlanning} onClick={() => void planImport()}>{isPlanning ? 'Planificando…' : 'Calcular plan de importación'}</button>

          {plan && (
            <section className="import-plan" aria-labelledby="import-plan-title">
              <h3 id="import-plan-title">3. Plan de importación</h3>
              <p>Nuevas: {plan.totals.new} · Idénticas: {plan.totals.identical} · Modificadas: {plan.totals.modified} · Bloqueadas: {plan.totals.blocked} · Excluidas: {plan.totals.excluded}</p>
              <ul className="history-list">
                {plan.revisions.map((revision) => (
                  <li key={revision.revision_index}>
                    <strong>{revision.label}</strong> — {classificationLabels[revision.classification]} ({revision.metric_count} valores)
                    {revision.issues.length > 0 && <span> · {revision.issues.join(', ')}</span>}
                    {revision.classification === 'modified' && <label className="decision-option"><input type="checkbox" checked={decisions.modifications.some((item) => item.revision_index === revision.revision_index && item.action === 'create_version')} onChange={(event) => setModificationAccepted(revision.revision_index, event.target.checked)} />Crear una nueva versión inmutable</label>}
                  </li>
                ))}
              </ul>
              <label className="decision-option"><input type="checkbox" checked={confirmationAccepted} disabled={plan.totals.blocked > 0 || hasUnacceptedModifications} onChange={(event) => setConfirmationAccepted(event.target.checked)} />Confirmo que he revisado el plan y deseo persistirlo</label>
              <button type="button" disabled={!confirmationAccepted || isConfirming || plan.totals.blocked > 0 || hasUnacceptedModifications} onClick={() => void confirmImport()}>{isConfirming ? 'Confirmando…' : 'Confirmar importación'}</button>
              {lastImport && <p className="success-message">Resultado: {lastImport.outcome}. Revisiones creadas: {lastImport.created_review_count}; versionadas: {lastImport.versioned_review_count}; omitidas: {lastImport.skipped_review_count}.</p>}
            </section>
          )}
        </div>
      )}

      <section className="measurement-section" aria-labelledby="history-title">
        <h3 id="history-title">Historial privado</h3>
        {historyState === 'loading' && <p role="status">Cargando historial…</p>}
        {historyState === 'error' && <button className="button-secondary" type="button" onClick={() => void loadHistory()}>Reintentar historial</button>}
        {historyState === 'ready' && displayedReviews.length === 0 && <p className="form-note">Todavía no hay revisiones para esta fuente.</p>}
        {historyState === 'ready' && displayedReviews.length > 0 && <><ul className="history-list">{pagedReviews.map((review) => <li key={review.id}><strong>{review.measurement_date}</strong> · versión {review.version} · {review.is_current ? 'vigente' : 'histórica'} · {review.metric_count} valores <button className="button-secondary button-compact" type="button" disabled={detailLoadingId === review.id} onClick={() => void openReview(review.id)}>{detailLoadingId === review.id ? 'Abriendo…' : 'Ver detalle'}</button></li>)}</ul><div className="form-actions"><button className="button-secondary button-compact" type="button" disabled={reviewPageIndex === 0} onClick={() => setReviewPageIndex((page) => page - 1)}>Revisiones anteriores</button><button className="button-secondary button-compact" type="button" disabled={(reviewPageIndex + 1) * historyPageSize >= displayedReviews.length} onClick={() => setReviewPageIndex((page) => page + 1)}>Más revisiones</button></div></>}

        {reviewDetail && <article className="review-detail"><h4>Detalle de {reviewDetail.measurement_date} · versión {reviewDetail.version}</h4><dl className="metric-list">{reviewDetail.values.map((value) => <div className="metric-list__item" key={value.id}><dt>{value.original_label}</dt><dd>{sideLabels[value.side]} · {value.value} {unitLabels[value.unit]}</dd></div>)}</dl></article>}

        <h4>Importaciones</h4>
        {historyState === 'ready' && displayedImports.length === 0 && <p className="form-note">No hay importaciones registradas.</p>}
        {historyState === 'ready' && displayedImports.length > 0 && <><ul className="history-list">{pagedImports.map((item) => <li key={item.id}><strong>{new Date(item.imported_at).toLocaleString()}</strong> · {item.outcome} · {item.status}{item.status === 'completed' && <button className="button-secondary button-compact" type="button" disabled={revertingId === item.id} onClick={() => void revertImport(item)}>{revertingId === item.id ? 'Revirtiendo…' : 'Revertir'}</button>}</li>)}</ul><div className="form-actions"><button className="button-secondary button-compact" type="button" disabled={importPageIndex === 0} onClick={() => setImportPageIndex((page) => page - 1)}>Importaciones anteriores</button><button className="button-secondary button-compact" type="button" disabled={(importPageIndex + 1) * historyPageSize >= displayedImports.length} onClick={() => setImportPageIndex((page) => page + 1)}>Más importaciones</button></div></>}
      </section>
    </section>
  )
}
