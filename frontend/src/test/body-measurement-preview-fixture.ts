import type { BodyMeasurementImportPreview } from '../services/body-measurement-import'

export const previewFixture: BodyMeasurementImportPreview = {
  adapter_version: 'body-measurements-v1',
  fingerprint: `sha256:${'a'.repeat(64)}`,
  metadata: {
    file_size_bytes: 1024,
    sheet_count: 1,
    supported_sheet: 'Revisiones',
    used_rows: 36,
    used_columns: 6,
    zip_entry_count: 12,
    uncompressed_size_bytes: 4096,
    content_type_signal: 'xlsx',
  },
  revisions: [
    {
      raw_date: '2026-01-15',
      normalized_date: '2026-01-15',
      label: '2026-01-15',
      date_status: 'resolved',
      inferred_year: null,
      metrics: [
        {
          code: 'body_weight',
          category: 'bioimpedance',
          side: 'none',
          value: '72.8',
          unit: 'kg',
          unit_source: 'excel',
          original_label: 'Peso corporal',
          origin: 'reported',
        },
        {
          code: 'thigh_circumference',
          category: 'circumference',
          side: 'left',
          value: '56.8',
          unit: 'cm',
          unit_source: 'excel',
          original_label: 'Muslo izquierdo',
          origin: 'reported',
        },
      ],
    },
  ],
  warnings: [
    {
      code: 'revision_year_inferred_candidate',
      message: 'Año propuesto, todavía sin resolver.',
      blocking: false,
      revision_label: '06-03 (año pendiente)',
      metric_code: null,
    },
  ],
  errors: [
    {
      code: 'revision_year_required',
      message: 'Falta el año de una revisión.',
      blocking: true,
      revision_label: '06-03 (año pendiente)',
      metric_code: null,
    },
  ],
  unknown_metrics: [
    {
      category_label: 'Otros',
      side: 'none',
      original_label: 'Índice experimental',
      populated_revision_count: 1,
    },
  ],
  ignored_cells: [],
  totals: {
    revision_count: 1,
    recognized_metric_values: 2,
    unknown_metric_rows: 1,
    ignored_cells: 0,
    warning_count: 1,
    error_count: 1,
    has_blocking_errors: true,
  },
}
