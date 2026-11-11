import type { ReactNode } from 'react'

export function Prose({ id, title, children }: { id?: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-6 border-t border-rule pt-6">
      <h2 className="text-xl font-bold tracking-tight">{title}</h2>
      <div className="mt-3 max-w-prose space-y-3 leading-relaxed">{children}</div>
    </section>
  )
}
