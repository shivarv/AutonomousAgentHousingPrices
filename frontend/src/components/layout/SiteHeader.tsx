import { NavLink } from 'react-router'

const NAV_ITEMS = [
  { to: '/', label: 'Site explorer', end: true },
  { to: '/overview', label: 'Overview', end: false },
  { to: '/methodology', label: 'Methodology & sources', end: false },
  { to: '/estimates', label: 'About the estimates', end: false },
] as const

export function SiteHeader() {
  return (
    <header className="bg-harbour brass-rule relative border-b-2 text-white">
      <div className="flex flex-col gap-3 px-4 py-3.5 md:flex-row md:items-center md:justify-between md:px-6">
        <NavLink to="/" className="group flex items-baseline gap-2">
          <span className="text-lg font-bold tracking-tight drop-shadow-sm">
            Massachusetts Housing Need
          </span>
          <span className="text-sm font-medium text-marker-light/90">and Site Finder</span>
        </NavLink>
        <nav aria-label="Main">
          <ul className="flex flex-wrap gap-x-1 gap-y-1 text-sm">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `block rounded-full px-3.5 py-1.5 font-medium transition-colors ${
                      isActive
                        ? 'btn-brass font-semibold'
                        : 'text-white/75 hover:bg-white/10 hover:text-white'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  )
}
