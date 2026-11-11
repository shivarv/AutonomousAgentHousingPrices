import { Link } from 'react-router'
import { PageContainer } from '@/components/layout/PageContainer'

export function NotFoundPage() {
  return (
    <PageContainer title="Page not found" intro="This address doesn't match any page.">
      <Link to="/" className="font-medium underline underline-offset-4">
        Go to the site explorer
      </Link>
    </PageContainer>
  )
}
