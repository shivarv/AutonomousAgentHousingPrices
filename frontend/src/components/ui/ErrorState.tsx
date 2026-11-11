interface ErrorStateProps {
  title?: string
  error: unknown
  onRetry?: () => void
}

export function ErrorState({ title = 'Something went wrong', error, onRetry }: ErrorStateProps) {
  const message = error instanceof Error ? error.message : 'Unknown error'
  return (
    <div role="alert" className="rounded-md border border-shortage/40 bg-paper-raised p-4">
      <p className="font-semibold text-shortage">{title}</p>
      <p className="mt-1 text-ink-soft">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-sm border border-rule px-3 py-1 text-sm font-medium hover:bg-paper"
        >
          Try again
        </button>
      )}
    </div>
  )
}
