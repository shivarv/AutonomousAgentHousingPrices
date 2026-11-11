/** Mirrors backend app/schemas/health.py */
export interface Health {
  status: 'ok' | 'degraded'
  database: 'ok' | 'unavailable'
  app: string
}
