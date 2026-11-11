import { PageContainer } from '@/components/layout/PageContainer'
import { AboutEstimates } from '@/features/methodology'

export function AboutEstimatesPage() {
  return (
    <PageContainer
      title="About the estimates"
      intro="Official homelessness counts are published only for each Continuum of Care. Figures for smaller areas on this site are modelled estimates that add up to those official totals."
    >
      <AboutEstimates />
    </PageContainer>
  )
}
