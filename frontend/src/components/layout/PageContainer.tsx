import type { ReactNode } from 'react'

interface PageContainerProps {
  title: string
  intro?: string
  children?: ReactNode
}

export function PageContainer({ title, intro, children }: PageContainerProps) {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-6 md:py-12">
      <h1 className="heading-mark text-3xl font-bold tracking-tight text-harbour md:text-4xl">
        {title}
      </h1>
      {intro && <p className="mt-3 max-w-prose text-lg text-ink-soft">{intro}</p>}
      <div className="mt-8">{children}</div>
    </div>
  )
}
