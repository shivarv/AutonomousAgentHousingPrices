import { useState } from 'react'
import type { PitYear } from '@/features/overview/types'
import { formatCount } from '@/utils/format'

const W = 640
const H = 240
const PAD = { top: 16, right: 16, bottom: 28, left: 56 }

/** Single-series line: official Point-in-Time total by year, with a hover read-out. */
export function HomelessTrendChart({ years, title }: { years: PitYear[]; title: string }) {
  const [hover, setHover] = useState<number | null>(null)
  if (years.length < 2) return <p className="text-ink-soft">Not enough years to draw a trend.</p>
  const xs = years.map((y) => y.year)
  const max = Math.max(...years.map((y) => y.total)) * 1.1
  const x = (yr: number) =>
    PAD.left + ((yr - xs[0]) / (xs.at(-1)! - xs[0])) * (W - PAD.left - PAD.right)
  const y = (v: number) => PAD.top + (1 - v / max) * (H - PAD.top - PAD.bottom)
  const path = years.map((p, i) => `${i ? 'L' : 'M'}${x(p.year)},${y(p.total)}`).join(' ')
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => Math.round((max * t) / 1000) * 1000)
  const active = hover === null ? years.at(-1)! : years[hover]
  return (
    <figure>
      <figcaption className="text-sm text-ink-soft">
        {title}. {active.year}: <strong className="text-ink">{formatCount(active.total)}</strong>{' '}
        people ({formatCount(active.sheltered)} sheltered, {formatCount(active.unsheltered)}{' '}
        unsheltered)
      </figcaption>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="mt-2 w-full"
        role="img"
        aria-label={`${title}: line chart from ${xs[0]} to ${xs.at(-1)}`}
        onMouseLeave={() => setHover(null)}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} className="stroke-rule" />
            <text x={PAD.left - 8} y={y(t) + 4} textAnchor="end" className="fill-ink-soft text-[11px]">
              {formatCount(t)}
            </text>
          </g>
        ))}
        {years.map((p) => (
          <text
            key={p.year}
            x={x(p.year)}
            y={H - 8}
            textAnchor="middle"
            className="fill-ink-soft text-[11px]"
          >
            {p.year % 2 === 0 ? p.year : ''}
          </text>
        ))}
        <path d={path} fill="none" strokeWidth={2} className="stroke-ink" />
        {years.map((p, i) => (
          <g key={p.year} onMouseEnter={() => setHover(i)} onFocus={() => setHover(i)}>
            <rect
              x={x(p.year) - 14}
              y={PAD.top}
              width={28}
              height={H - PAD.top - PAD.bottom}
              fill="transparent"
            />
            <circle
              cx={x(p.year)}
              cy={y(p.total)}
              r={active.year === p.year ? 5 : 3}
              className="fill-ink stroke-paper-raised"
              strokeWidth={2}
            />
          </g>
        ))}
      </svg>
    </figure>
  )
}
