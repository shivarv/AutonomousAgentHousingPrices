import { createBrowserRouter } from 'react-router'
import { AppShell } from '@/components/layout/AppShell'
import { AboutEstimatesPage } from '@/pages/AboutEstimatesPage'
import { ExplorerPage } from '@/pages/ExplorerPage'
import { MethodologyPage } from '@/pages/MethodologyPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { OverviewPage } from '@/pages/OverviewPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <ExplorerPage /> },
      { path: 'overview', element: <OverviewPage /> },
      { path: 'methodology', element: <MethodologyPage /> },
      { path: 'estimates', element: <AboutEstimatesPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
