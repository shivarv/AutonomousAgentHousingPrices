import { PageContainer } from '@/components/layout/PageContainer'
import { Overview } from '@/features/overview'

export function OverviewPage() {
  return (
    <PageContainer
      title="The picture in Massachusetts"
      intro="Homelessness, the affordable housing shortage and candidate construction sites, for the state, a county or a town."
    >
      <Overview />
    </PageContainer>
  )
}
