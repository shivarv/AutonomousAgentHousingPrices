import type { ExplorerMode } from '@/features/site-explorer/types'

const MODES: { value: ExplorerMode; label: string }[] = [
  { value: 'areas', label: 'Areas' },
  { value: 'rings', label: 'Rings' },
]

export function ModeToggle({ mode, onChange }: { mode: ExplorerMode; onChange: (m: ExplorerMode) => void }) {
  return (
    <div role="radiogroup" aria-label="How to add up the numbers" className="inline-flex gap-0.5 rounded-lg bg-paper-deep p-0.5 shadow-[inset_0_1px_2px_rgb(15_42_64/0.15)]">
      {MODES.map((m) => (
        <button
          key={m.value}
          type="button"
          role="radio"
          aria-checked={mode === m.value}
          onClick={() => onChange(m.value)}
          className={`rounded-md px-4 py-1.5 text-sm font-semibold transition-colors ${mode === m.value ? 'btn-ink' : 'text-ink-soft hover:text-ink'}`}
        >
          {m.label}
        </button>
      ))}
    </div>
  )
}
