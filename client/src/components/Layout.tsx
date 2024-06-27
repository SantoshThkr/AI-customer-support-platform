import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { UserRole } from '../types/user'

interface NavItem {
  to: string
  label: string
  roles: UserRole[]
  end?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', roles: ['CUSTOMER'] },
  { to: '/dashboard', label: 'Queue', roles: ['AGENT', 'ADMIN'] },
  { to: '/tickets', label: 'My tickets', roles: ['CUSTOMER'], end: true },
  { to: '/tickets/new', label: 'New ticket', roles: ['CUSTOMER'] },
  { to: '/tickets', label: 'All tickets', roles: ['AGENT', 'ADMIN'], end: true },
  { to: '/admin', label: 'Analytics', roles: ['ADMIN'], end: true },
  { to: '/admin/users', label: 'Users', roles: ['ADMIN'] },
]

function navClass({ isActive }: { isActive: boolean }) {
  return `whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium ${
    isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
  }`
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) {
    return null
  }

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const items = NAV_ITEMS.filter((item) => item.roles.includes(user.role))

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <span className="text-lg font-semibold text-indigo-700">Support Desk</span>
          <nav className="order-last -mx-1 flex w-full gap-1 overflow-x-auto md:order-none md:w-auto">
            {items.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="hidden text-slate-600 sm:inline">
              {user.name}
              <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">
                {user.role.toLowerCase()}
              </span>
            </span>
            <button type="button" onClick={handleLogout} className="btn-secondary">
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
