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
    <div className="border-l-2 border-rule pl-3">
      <dt className="text-sm text-ink-soft">{label}</dt>
      <dd className={`text-2xl font-bold tabular-nums ${TONE[tone]}`}>{value}</dd>
      {detail && <dd className="mt-0.5 text-xs text-ink-soft">{detail}</dd>}
    </div>
  )
}
