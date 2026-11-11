export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <p className="flex items-center gap-2 py-4 text-ink-soft" role="status" aria-live="polite">
      <span className="size-3 animate-spin rounded-full border-2 border-rule border-t-ink" />
      {label}…
    </p>
  )
}
