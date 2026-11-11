import { Link } from 'react-router'

/** Small tag that says whether a homeless number is an estimate or an official count. */
export function FigureLabel({ label }: { label: 'estimate' | 'official CoC count' }) {
  if (label === 'estimate') {
    return (
      <Link
        to="/estimates"
        className="rounded-sm bg-estimate/10 px-1.5 py-0.5 text-xs font-semibold text-estimate underline-offset-2 hover:underline"
        title="Modelled estimate: how it is made"
      >
        estimate
      </Link>
    )
  }
  return (
    <span className="rounded-sm bg-ink/10 px-1.5 py-0.5 text-xs font-semibold text-ink">
      official CoC count
    </span>
  )
}
