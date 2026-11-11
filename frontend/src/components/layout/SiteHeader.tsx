import { NavLink } from 'react-router'

const NAV_ITEMS = [
  { to: '/', label: 'Site explorer', end: true },
  { to: '/overview', label: 'Overview', end: false },
  { to: '/methodology', label: 'Methodology & sources', end: false },
  { to: '/estimates', label: 'About the estimates', end: false },
] as const

export function SiteHeader() {
  return (
    <header className="border-b border-rule bg-paper-raised">
      <div className="flex flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between md:px-6">
        <NavLink to="/" className="flex items-baseline gap-2 text-ink">
          <span className="text-lg font-bold tracking-tight">Massachusetts Housing Need</span>
          <span className="text-sm font-medium text-ink-soft">and Site Finder</span>
        </NavLink>
        <nav aria-label="Main">
          <ul className="flex flex-wrap gap-x-1 gap-y-1 text-sm">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `block rounded-sm px-3 py-1.5 font-medium ${
                      isActive
                        ? 'bg-ink text-paper-raised'
                        : 'text-ink-soft hover:bg-paper hover:text-ink'
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
