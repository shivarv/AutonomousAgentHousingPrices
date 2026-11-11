import type { ExplorerMode } from '@/features/site-explorer/types'

const MODES: { value: ExplorerMode; label: string }[] = [
  { value: 'areas', label: 'Areas' },
  { value: 'rings', label: 'Rings' },
]

export function ModeToggle({ mode, onChange }: { mode: ExplorerMode; onChange: (m: ExplorerMode) => void }) {
  return (
    <div role="radiogroup" aria-label="How to add up the numbers" className="inline-flex rounded-sm border border-ink">
      {MODES.map((m) => (
        <button
          key={m.value}
          type="button"
          role="radio"
          aria-checked={mode === m.value}
          onClick={() => onChange(m.value)}
          className={`px-4 py-1.5 text-sm font-semibold ${mode === m.value ? 'bg-ink text-paper-raised' : 'bg-paper-raised text-ink'}`}
        >
          {m.label}
        </button>
      ))}
    </div>
  )
}
