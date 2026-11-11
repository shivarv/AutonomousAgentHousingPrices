import { useState } from 'react'
import { useGeocode } from '@/features/site-explorer/hooks/useExplorerData'
import type { LatLon } from '@/features/site-explorer/types'

export function AddressSearch({ onFound }: { onFound: (p: LatLon) => void }) {
  const [q, setQ] = useState('')
  const geo = useGeocode()
  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!q.trim()) return
    geo.mutate(q, {
      onSuccess: (r) => {
        const m = r.matches[0]
        if (m) onFound({ lat: m.lat, lon: m.lon })
      },
    })
  }
  const noMatch = geo.data && geo.data.matches.length === 0
  return (
    <form onSubmit={submit} className="flex min-w-0 flex-col gap-1" role="search">
      <label htmlFor="address" className="text-sm font-medium text-ink-soft">
        Address search
      </label>
      <div className="flex gap-1">
        <input
          id="address"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="e.g. 1 City Hall Sq, Boston"
          className="min-w-0 flex-1 rounded-md border border-rule bg-paper-raised px-2.5 py-1.5 text-sm"
        />
        <button
          type="submit"
          disabled={geo.isPending}
          className="btn-ink rounded-md px-3.5 py-1.5 text-sm font-medium disabled:opacity-60"
        >
          {geo.isPending ? 'Searching' : 'Search'}
        </button>
      </div>
      <p className="min-h-4 text-xs text-ink-soft" aria-live="polite">
        {geo.isError && (geo.error as Error).message}
        {noMatch && 'No Massachusetts address matched; try adding the town.'}
        {geo.data?.matches[0] && `Found: ${geo.data.matches[0].address}`}
      </p>
    </form>
  )
}
