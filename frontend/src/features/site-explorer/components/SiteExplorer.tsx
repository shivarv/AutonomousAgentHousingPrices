import { BaseMap } from '@/features/site-explorer/components/BaseMap'

export function SiteExplorer() {
  return (
    <div className="flex flex-1 flex-col lg:flex-row">
      <section className="relative flex min-h-[60vh] flex-1" aria-label="Map">
        <BaseMap />
      </section>
      <aside
        className="w-full border-t border-rule bg-paper-raised p-4 lg:w-96 lg:border-t-0 lg:border-l"
        aria-label="Area details"
      >
        <h1 className="text-xl font-bold tracking-tight">Site explorer</h1>
        <p className="mt-2 text-ink-soft">
          Choose a place on the map to see estimated homelessness, at-risk households and the
          affordable housing shortage around it.
        </p>
      </aside>
    </div>
  )
}
