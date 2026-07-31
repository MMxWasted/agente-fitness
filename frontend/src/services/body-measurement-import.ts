import {
  ApiError,
  getApiBaseUrl,
  type AuthenticatedOperation,
} from './api'

export const BODY_MEASUREMENT_FILE_MAX_BYTES = 5 * 1024 * 1024

export type MeasurementCategory =
  | 'bioimpedance'
  | 'skinfold'
  | 'circumference'
export type MeasurementSide = 'none' | 'left' | 'right'
export type MeasurementUnit =
  | 'kg'
  | 'cm'
  | 'mm'
  | 'percent'
  | 'kcal_per_day'
  | 'years'
  | 'unitless_index'
  | 'unitless_level'
export type UnitSource = 'excel' | 'adapter_v1' | 'unresolved'

export interface PreviewIssue {
  code: string
  message: string
  blocking: boolean
  revision_label: string | null
  metric_code: string | null
}

export interface MeasurementPreview {
  code: string
  category: MeasurementCategory
  side: MeasurementSide
  value: string
  unit: MeasurementUnit | null
  unit_source: UnitSource
  original_label: string
  origin: 'reported'
}

export interface RevisionPreview {
  raw_date: string
  normalized_date: string | null
  label: string
  date_status: 'resolved' | 'missing_year'
  inferred_year: number | null
  metrics: MeasurementPreview[]
}

export interface BodyMeasurementImportPreview {
  adapter_version: 'body-measurements-v1'
  fingerprint: string
  metadata: {
    file_size_bytes: number
    sheet_count: number
    supported_sheet: string
    used_rows: number
    used_columns: number
    zip_entry_count: number
    uncompressed_size_bytes: number
    content_type_signal: 'xlsx' | 'generic' | 'missing'
  }
  revisions: RevisionPreview[]
  warnings: PreviewIssue[]
  errors: PreviewIssue[]
  unknown_metrics: Array<{
    category_label: string
    side: MeasurementSide
    original_label: string
    populated_revision_count: number
  }>
  ignored_cells: Array<{
    reference: string
    reason:
      | 'empty_metric_value'
      | 'separator_row'
      | 'unsupported_section'
  }>
  totals: {
    revision_count: number
    recognized_metric_values: number
    unknown_metric_rows: number
    ignored_cells: number
    warning_count: number
    error_count: number
    has_blocking_errors: boolean
  }
}

export type FileValidationResult =
  | { valid: true }
  | { valid: false; message: string }

export function validateBodyMeasurementFile(
  file: File,
): FileValidationResult {
  if (!file.name.toLowerCase().endsWith('.xlsx')) {
    return {
      valid: false,
      message: 'Selecciona un archivo .xlsx sin macros.',
    }
  }
  if (file.size > BODY_MEASUREMENT_FILE_MAX_BYTES) {
    return {
      valid: false,
      message: 'El archivo supera el límite de 5 MiB.',
    }
  }
  if (file.size === 0) {
    return {
      valid: false,
      message: 'El archivo está vacío.',
    }
  }
  return { valid: true }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isPreviewIssue(value: unknown): value is PreviewIssue {
  return (
    isRecord(value) &&
    typeof value.code === 'string' &&
    typeof value.message === 'string' &&
    typeof value.blocking === 'boolean' &&
    (value.revision_label === null ||
      typeof value.revision_label === 'string') &&
    (value.metric_code === null || typeof value.metric_code === 'string')
  )
}

function isMeasurementCategory(
  value: unknown,
): value is MeasurementCategory {
  return ['bioimpedance', 'skinfold', 'circumference'].includes(
    String(value),
  )
}

function isMeasurementSide(value: unknown): value is MeasurementSide {
  return ['none', 'left', 'right'].includes(String(value))
}

function isMeasurementUnit(
  value: unknown,
): value is MeasurementUnit {
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

function isMeasurement(value: unknown): value is MeasurementPreview {
  return (
    isRecord(value) &&
    typeof value.code === 'string' &&
    isMeasurementCategory(value.category) &&
    isMeasurementSide(value.side) &&
    typeof value.value === 'string' &&
    (value.unit === null || isMeasurementUnit(value.unit)) &&
    ['excel', 'adapter_v1', 'unresolved'].includes(
      String(value.unit_source),
    ) &&
    typeof value.original_label === 'string' &&
    value.origin === 'reported'
  )
}

function isRevision(value: unknown): value is RevisionPreview {
  return (
    isRecord(value) &&
    typeof value.raw_date === 'string' &&
    (value.normalized_date === null ||
      typeof value.normalized_date === 'string') &&
    typeof value.label === 'string' &&
    ['resolved', 'missing_year'].includes(String(value.date_status)) &&
    (value.inferred_year === null ||
      typeof value.inferred_year === 'number') &&
    Array.isArray(value.metrics) &&
    value.metrics.every(isMeasurement)
  )
}

function isUnknownMetric(value: unknown): boolean {
  return (
    isRecord(value) &&
    typeof value.category_label === 'string' &&
    isMeasurementSide(value.side) &&
    typeof value.original_label === 'string' &&
    typeof value.populated_revision_count === 'number'
  )
}

function isIgnoredCell(value: unknown): boolean {
  return (
    isRecord(value) &&
    typeof value.reference === 'string' &&
    [
      'empty_metric_value',
      'separator_row',
      'unsupported_section',
    ].includes(String(value.reason))
  )
}

function isBodyMeasurementImportPreview(
  value: unknown,
): value is BodyMeasurementImportPreview {
  return (
    isRecord(value) &&
    value.adapter_version === 'body-measurements-v1' &&
    typeof value.fingerprint === 'string' &&
    /^sha256:[0-9a-f]{64}$/.test(value.fingerprint) &&
    isRecord(value.metadata) &&
    typeof value.metadata.file_size_bytes === 'number' &&
    typeof value.metadata.sheet_count === 'number' &&
    typeof value.metadata.supported_sheet === 'string' &&
    typeof value.metadata.used_rows === 'number' &&
    typeof value.metadata.used_columns === 'number' &&
    typeof value.metadata.zip_entry_count === 'number' &&
    typeof value.metadata.uncompressed_size_bytes === 'number' &&
    ['xlsx', 'generic', 'missing'].includes(
      String(value.metadata.content_type_signal),
    ) &&
    Array.isArray(value.revisions) &&
    value.revisions.every(isRevision) &&
    Array.isArray(value.warnings) &&
    value.warnings.every(isPreviewIssue) &&
    Array.isArray(value.errors) &&
    value.errors.every(isPreviewIssue) &&
    Array.isArray(value.unknown_metrics) &&
    value.unknown_metrics.every(isUnknownMetric) &&
    Array.isArray(value.ignored_cells) &&
    value.ignored_cells.every(isIgnoredCell) &&
    isRecord(value.totals) &&
    typeof value.totals.revision_count === 'number' &&
    typeof value.totals.recognized_metric_values === 'number' &&
    typeof value.totals.unknown_metric_rows === 'number' &&
    typeof value.totals.ignored_cells === 'number' &&
    typeof value.totals.warning_count === 'number' &&
    typeof value.totals.error_count === 'number' &&
    typeof value.totals.has_blocking_errors === 'boolean'
  )
}

export function previewBodyMeasurements(
  file: File,
): AuthenticatedOperation<BodyMeasurementImportPreview> {
  return async (accessToken) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(
      `${getApiBaseUrl()}/api/v1/body-measurement-imports/preview`,
      {
        method: 'POST',
        credentials: 'omit',
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
      },
    )
    if (!response.ok) {
      throw new ApiError(
        response.status,
        'Body measurement preview request failed',
      )
    }

    const payload: unknown = await response.json()
    if (!isBodyMeasurementImportPreview(payload)) {
      throw new Error(
        'Body measurement preview does not match the contract',
      )
    }
    return payload
  }
}
