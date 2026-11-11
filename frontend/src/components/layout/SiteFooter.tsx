import { ApiStatus } from '@/features/system'

export function SiteFooter() {
  return (
    <footer className="flex flex-col gap-2 border-t border-rule bg-paper-raised px-4 py-3 text-sm text-ink-soft md:flex-row md:items-center md:justify-between md:px-6">
      <p>
        Public data only. Tract-level homelessness figures are modelled estimates; official counts
        exist only per Continuum of Care.
      </p>
      <ApiStatus />
    </footer>
  )
}
