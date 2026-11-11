import { useHealth } from '@/features/system/hooks/useHealth'

export function ApiStatus() {
  const { data, isPending, isError } = useHealth()

  let label = 'Checking the data service'
  let dot = 'bg-rule'
  if (isError) {
    label = 'Data service unreachable'
    dot = 'bg-shortage'
  } else if (data) {
    const ok = data.status === 'ok'
    label = ok ? 'Data service online' : 'Data service online, database unavailable'
    dot = ok ? 'bg-surplus' : 'bg-marker'
  }

  return (
    <p className="flex items-center gap-2 text-sm text-ink-soft" role="status" aria-live="polite">
      <span className={`size-2 rounded-full ${dot} ${isPending ? 'animate-pulse' : ''}`} />
      {label}
    </p>
  )
}
