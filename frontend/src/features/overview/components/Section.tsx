import type { ReactNode } from 'react'

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-rule pt-6">
      <h2 className="text-xl font-bold tracking-tight">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  )
}
