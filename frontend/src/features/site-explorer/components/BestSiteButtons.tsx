interface BestSiteButtonsProps {
  offset: number | null
  loading: boolean
  onShow: (offset: number) => void
}

export function BestSiteButtons({ offset, loading, onShow }: BestSiteButtonsProps) {
  return (
    <div className="flex items-end gap-2">
      <button
        type="button"
        onClick={() => onShow(0)}
        disabled={loading}
        className="rounded-sm bg-marker px-3 py-1.5 text-sm font-bold text-ink shadow-xs hover:brightness-95 disabled:opacity-60"
      >
        Show best location
      </button>
      <button
        type="button"
        onClick={() => onShow((offset ?? -1) + 1)}
        disabled={loading || offset === null}
        className="rounded-sm border border-rule bg-paper-raised px-3 py-1.5 text-sm font-medium disabled:opacity-50"
      >
        Next best{offset !== null ? ` (#${offset + 2})` : ''}
      </button>
    </div>
  )
}
