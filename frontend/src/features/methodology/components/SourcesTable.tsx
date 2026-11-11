import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { LoadingState } from '@/components/ui/LoadingState'
import { useSources } from '@/features/methodology/hooks/useMethodology'

export function SourcesTable() {
  const { data, isPending, isError, error } = useSources()
  if (isPending) return <LoadingState label="Loading data sources" />
  if (isError) return <ErrorState error={error} />
  if (!data.length) return <EmptyState title="No data sources registered" />
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[44rem] text-sm">
        <caption className="sr-only">Datasets used, with years, geography and licence</caption>
        <thead className="border-b border-rule text-left text-ink-soft">
          <tr>
            <th scope="col" className="py-2 font-medium">Dataset</th>
            <th scope="col" className="py-2 font-medium">Years</th>
            <th scope="col" className="py-2 font-medium">Geography</th>
            <th scope="col" className="py-2 font-medium">Downloaded</th>
            <th scope="col" className="py-2 font-medium">Licence or terms</th>
          </tr>
        </thead>
        <tbody>
          {data.map((s) => (
            <tr key={s.key} className="border-b border-rule/60 align-top">
              <th scope="row" className="py-1.5 pr-3 text-left font-normal">
                <a href={s.url} className="font-medium underline-offset-2 hover:underline" rel="noreferrer" target="_blank">
                  {s.name}
                </a>
                <span className="block text-xs text-ink-soft">key: {s.key}</span>
              </th>
              <td className="py-1.5 pr-3">{s.years}</td>
              <td className="py-1.5 pr-3">{s.geography}</td>
              <td className="whitespace-nowrap py-1.5 pr-3 tabular-nums">{s.download_date}</td>
              <td className="py-1.5">{s.licence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
