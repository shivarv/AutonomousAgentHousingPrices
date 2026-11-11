export interface DataSource {
  id: number
  key: string
  name: string
  url: string
  download_date: string
  licence: string
  geography: string
  years: string
  file_path: string
  columns_used: string
}

export interface ModelRun {
  id: number
  kind: string
  created_at: string
  params: Record<string, unknown>
  metrics: Record<string, unknown>
  artifact_path: string | null
  notes: string | null
}

export interface ModelMetrics {
  home_value: ModelRun | null
  site_scoring: ModelRun | null
}
