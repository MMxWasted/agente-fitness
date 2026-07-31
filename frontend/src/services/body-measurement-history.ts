import {
  ApiError,
  getApiBaseUrl,
  type AuthenticatedOperation,
} from './api'
import type {
  BodyMeasurementImportPreview,
  MeasurementCategory,
  MeasurementSide,
  MeasurementUnit,
} from './body-measurement-import'

export interface BodyMeasurementSource {
  id: string
  display_name: string
  source_kind: 'manual_excel'
  logical_key: string
  history_version: number
  created_at: string
  updated_at: string
}

export interface BodyMeasurementImportDecisions {
  date_resolutions: Array<{
    revision_index: number
    measurement_date: string
  }>
  unit_resolutions: Array<{
    metric_code: string
    side: MeasurementSide
    action: 'accept_canonical'
  }>
  excluded_revisions: number[]
  excluded_metrics: Array<{
    revision_index: number
    metric_code: string
    side: MeasurementSide
  }>
  excluded_unknown_metrics: Array<{
    category_label: string
    original_label: string
    side: MeasurementSide
  }>
  disambiguators: Array<{
    revision_index: number
    disambiguator: string
  }>
  modifications: Array<{
    revision_index: number
    action: 'reject' | 'create_version'
  }>
}

export type ImportPlanClassification =
  | 'new'
  | 'identical'
  | 'modified'
  | 'blocked'
  | 'excluded'

export interface BodyMeasurementImportPlan {
  source_id: string
  history_version: number
  confirmed_fingerprint: string
  revisions: Array<{
    revision_index: number
    label: string
    measurement_date: string | null
    disambiguator: string
    classification: ImportPlanClassification
    metric_count: number
    current_review_id: string | null
    current_version: number | null
    issues: string[]
  }>
  totals: Record<ImportPlanClassification, number>
}

export interface BodyMeasurementImportRecord {
  id: string
  source_id: string
  status: 'completed' | 'reverted'
  adapter_version: string
  outcome: 'created' | 'skipped' | 'versioned' | 'mixed' | 'partial' | 'excluded'
  created_review_count: number
  skipped_review_count: number
  versioned_review_count: number
  excluded_review_count: number
  imported_at: string
  reverted_at: string | null
}

export interface BodyMeasurementReview {
  id: string
  source_id: string
  import_id: string
  measurement_date: string
  original_label: string
  normalized_label: string
  disambiguator: string
  version: number
  supersedes_review_id: string | null
  is_current: boolean
  metric_count: number
  created_at: string
}

export interface BodyMeasurementReviewDetail
  extends BodyMeasurementReview {
  values: Array<{
    id: string
    metric_code: string
    category: MeasurementCategory
    side: MeasurementSide
    value: string
    unit: MeasurementUnit
    original_label: string
    origin: 'reported'
    catalog_version: string
  }>
}

interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isCategory(value: unknown): value is MeasurementCategory {
  return ['bioimpedance', 'skinfold', 'circumference'].includes(String(value))
}

function isSide(value: unknown): value is MeasurementSide {
  return ['none', 'left', 'right'].includes(String(value))
}

function isUnit(value: unknown): value is MeasurementUnit {
  return [
    'kg',
    'cm',
    'mm',
    'percent',
    'kcal_per_day',
    'years',
    'unitless_index',
    'unitless_level',
  ].includes(String(value))
}

function isSource(value: unknown): value is BodyMeasurementSource {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    typeof value.display_name === 'string' &&
    value.source_kind === 'manual_excel' &&
    typeof value.logical_key === 'string' &&
    typeof value.history_version === 'number' &&
    typeof value.created_at === 'string' &&
    typeof value.updated_at === 'string'
  )
}

function isImport(value: unknown): value is BodyMeasurementImportRecord {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    typeof value.source_id === 'string' &&
    ['completed', 'reverted'].includes(String(value.status)) &&
    typeof value.adapter_version === 'string' &&
    ['created', 'skipped', 'versioned', 'mixed', 'partial', 'excluded'].includes(
      String(value.outcome),
    ) &&
    typeof value.created_review_count === 'number' &&
    typeof value.skipped_review_count === 'number' &&
    typeof value.versioned_review_count === 'number' &&
    typeof value.excluded_review_count === 'number' &&
    typeof value.imported_at === 'string' &&
    (value.reverted_at === null || typeof value.reverted_at === 'string')
  )
}

function isReview(value: unknown): value is BodyMeasurementReview {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    typeof value.source_id === 'string' &&
    typeof value.import_id === 'string' &&
    typeof value.measurement_date === 'string' &&
    typeof value.original_label === 'string' &&
    typeof value.normalized_label === 'string' &&
    typeof value.disambiguator === 'string' &&
    typeof value.version === 'number' &&
    (value.supersedes_review_id === null ||
      typeof value.supersedes_review_id === 'string') &&
    typeof value.is_current === 'boolean' &&
    typeof value.metric_count === 'number' &&
    typeof value.created_at === 'string'
  )
}

function isPage<T>(
  value: unknown,
  itemGuard: (item: unknown) => item is T,
): value is Page<T> {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(itemGuard) &&
    typeof value.total === 'number' &&
    typeof value.limit === 'number' &&
    typeof value.offset === 'number'
  )
}

function isPlan(value: unknown): value is BodyMeasurementImportPlan {
  if (!isRecord(value) || !isRecord(value.totals)) {
    return false
  }
  const totals = value.totals
  return (
    typeof value.source_id === 'string' &&
    typeof value.history_version === 'number' &&
    typeof value.confirmed_fingerprint === 'string' &&
    Array.isArray(value.revisions) &&
    value.revisions.every(
      (item) =>
        isRecord(item) &&
        typeof item.revision_index === 'number' &&
        typeof item.label === 'string' &&
        (item.measurement_date === null ||
          typeof item.measurement_date === 'string') &&
        typeof item.disambiguator === 'string' &&
        ['new', 'identical', 'modified', 'blocked', 'excluded'].includes(
          String(item.classification),
        ) &&
        typeof item.metric_count === 'number' &&
        (item.current_review_id === null ||
          typeof item.current_review_id === 'string') &&
        (item.current_version === null ||
          typeof item.current_version === 'number') &&
        Array.isArray(item.issues) &&
        item.issues.every((issue) => typeof issue === 'string'),
    ) &&
    ['new', 'identical', 'modified', 'blocked', 'excluded'].every(
      (key) => typeof totals[key] === 'number',
    )
  )
}

function isReviewDetail(value: unknown): value is BodyMeasurementReviewDetail {
  return (
    isReview(value) &&
    'values' in value &&
    Array.isArray(value.values) &&
    value.values.every(
      (item) =>
        isRecord(item) &&
        typeof item.id === 'string' &&
        typeof item.metric_code === 'string' &&
        isCategory(item.category) &&
        isSide(item.side) &&
        typeof item.value === 'string' &&
        isUnit(item.unit) &&
        typeof item.original_label === 'string' &&
        item.origin === 'reported' &&
        typeof item.catalog_version === 'string',
    )
  )
}

async function readJson<T>(
  response: Response,
  guard: (value: unknown) => value is T,
  label: string,
): Promise<T> {
  if (!response.ok) {
    throw new ApiError(response.status, `${label} request failed`)
  }
  const payload: unknown = await response.json()
  if (!guard(payload)) {
    throw new Error(`${label} response does not match the contract`)
  }
  return payload
}

function bearer(accessToken: string): Record<string, string> {
  return {
    Accept: 'application/json',
    Authorization: `Bearer ${accessToken}`,
  }
}

function importForm(
  file: File,
  sourceId: string,
  previewFingerprint: string,
  decisions: BodyMeasurementImportDecisions,
): FormData {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('source_id', sourceId)
  formData.append('preview_fingerprint', previewFingerprint)
  formData.append('decisions', JSON.stringify(decisions))
  return formData
}

export const emptyImportDecisions = (): BodyMeasurementImportDecisions => ({
  date_resolutions: [],
  unit_resolutions: [],
  excluded_revisions: [],
  excluded_metrics: [],
  excluded_unknown_metrics: [],
  disambiguators: [],
  modifications: [],
})

export const listBodyMeasurementSources: AuthenticatedOperation<
  Page<BodyMeasurementSource>
> = async (accessToken) => {
  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/body-measurement-sources?limit=100`,
    { credentials: 'omit', headers: bearer(accessToken) },
  )
  return readJson(
    response,
    (value): value is Page<BodyMeasurementSource> => isPage(value, isSource),
    'Body measurement sources',
  )
}

export function createBodyMeasurementSource(
  displayName: string,
  logicalKey: string,
): AuthenticatedOperation<BodyMeasurementSource> {
  return async (accessToken) => {
    const response = await fetch(
      `${getApiBaseUrl()}/api/v1/body-measurement-sources`,
      {
        method: 'POST',
        credentials: 'omit',
        headers: {
          ...bearer(accessToken),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          display_name: displayName,
          logical_key: logicalKey,
          source_kind: 'manual_excel',
        }),
      },
    )
    return readJson(response, isSource, 'Body measurement source')
  }
}

export function planBodyMeasurementImport(
  file: File,
  sourceId: string,
  preview: BodyMeasurementImportPreview,
  decisions: BodyMeasurementImportDecisions,
): AuthenticatedOperation<BodyMeasurementImportPlan> {
  return async (accessToken) => {
    const response = await fetch(
      `${getApiBaseUrl()}/api/v1/body-measurement-imports/plan`,
      {
        method: 'POST',
        credentials: 'omit',
        headers: bearer(accessToken),
        body: importForm(file, sourceId, preview.fingerprint, decisions),
      },
    )
    return readJson(response, isPlan, 'Body measurement import plan')
  }
}

export function confirmBodyMeasurementImport(
  file: File,
  sourceId: string,
  preview: BodyMeasurementImportPreview,
  plan: BodyMeasurementImportPlan,
  decisions: BodyMeasurementImportDecisions,
  idempotencyKey: string,
): AuthenticatedOperation<BodyMeasurementImportRecord> {
  return async (accessToken) => {
    const formData = importForm(
      file,
      sourceId,
      preview.fingerprint,
      decisions,
    )
    formData.append('confirmed_fingerprint', plan.confirmed_fingerprint)
    formData.append('history_version', String(plan.history_version))
    const response = await fetch(
      `${getApiBaseUrl()}/api/v1/body-measurement-imports`,
      {
        method: 'POST',
        credentials: 'omit',
        headers: {
          ...bearer(accessToken),
          'Idempotency-Key': idempotencyKey,
        },
        body: formData,
      },
    )
    return readJson(response, isImport, 'Body measurement import')
  }
}

export const listBodyMeasurementImports: AuthenticatedOperation<
  Page<BodyMeasurementImportRecord>
> = async (accessToken) => {
  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/body-measurement-imports?limit=100`,
    { credentials: 'omit', headers: bearer(accessToken) },
  )
  return readJson(
    response,
    (value): value is Page<BodyMeasurementImportRecord> => isPage(value, isImport),
    'Body measurement imports',
  )
}

export const listBodyMeasurementReviews: AuthenticatedOperation<
  Page<BodyMeasurementReview>
> = async (accessToken) => {
  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/body-measurement-reviews?limit=100`,
    { credentials: 'omit', headers: bearer(accessToken) },
  )
  return readJson(
    response,
    (value): value is Page<BodyMeasurementReview> => isPage(value, isReview),
    'Body measurement reviews',
  )
}

export function getBodyMeasurementReview(
  reviewId: string,
): AuthenticatedOperation<BodyMeasurementReviewDetail> {
  return async (accessToken) => {
    const response = await fetch(
      `${getApiBaseUrl()}/api/v1/body-measurement-reviews/${encodeURIComponent(reviewId)}`,
      { credentials: 'omit', headers: bearer(accessToken) },
    )
    return readJson(response, isReviewDetail, 'Body measurement review')
  }
}

export function revertBodyMeasurementImport(
  importId: string,
): AuthenticatedOperation<void> {
  return async (accessToken) => {
    const response = await fetch(
      `${getApiBaseUrl()}/api/v1/body-measurement-imports/${encodeURIComponent(importId)}`,
      {
        method: 'DELETE',
        credentials: 'omit',
        headers: bearer(accessToken),
      },
    )
    if (!response.ok) {
      throw new ApiError(response.status, 'Body measurement reversal failed')
    }
  }
}
