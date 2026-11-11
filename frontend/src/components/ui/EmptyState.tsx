import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  children?: ReactNode
}

export function EmptyState({ title, children }: EmptyStateProps) {
  return (
    <div className="rounded-md border border-dashed border-rule bg-paper-raised p-6">
      <h2 className="text-base font-semibold">{title}</h2>
      {children && <div className="mt-2 max-w-prose text-ink-soft">{children}</div>}
    </div>
  )
}
