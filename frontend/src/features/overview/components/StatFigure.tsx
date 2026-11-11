import type { ReactNode } from 'react'

interface StatFigureProps {
  label: string
  value: string
  detail?: ReactNode
  tone?: 'default' | 'shortage' | 'surplus'
}

const TONE = { default: 'text-ink', shortage: 'text-shortage', surplus: 'text-surplus' }

export function StatFigure({ label, value, detail, tone = 'default' }: StatFigureProps) {
  return (
    <div className="surface-plate relative overflow-hidden rounded-lg py-3 pr-3 pl-4 before:absolute before:inset-y-0 before:left-0 before:w-1 before:bg-linear-to-b before:from-marker-light before:to-harbour-light">
      <dt className="text-sm text-ink-soft">{label}</dt>
      <dd className={`text-2xl font-bold tabular-nums ${TONE[tone]}`}>{value}</dd>
      {detail && <dd className="mt-0.5 text-xs text-ink-soft">{detail}</dd>}
    </div>
  )
}
