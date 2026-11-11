import { PageContainer } from '@/components/layout/PageContainer'
import { Methodology } from '@/features/methodology'

export function MethodologyPage() {
  return (
    <PageContainer
      title="Methodology & sources"
      intro="Where every number comes from, how it was cleaned and how the indicators are calculated."
    >
      <Methodology />
    </PageContainer>
  )
}
