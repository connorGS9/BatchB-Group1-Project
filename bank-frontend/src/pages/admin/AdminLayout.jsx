import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { API_ORIGIN } from '../../api/authService.js'
import { useAuth } from '../../auth.jsx'
import ThemeToggle from '../../components/ThemeToggle.jsx'

const NAV = [
  { to: '/admin', label: 'Overview', end: true },
  { to: '/admin/applications', label: 'Applications' },
  { to: '/admin/accounts', label: 'Accounts' },
  { to: '/admin/customers', label: 'Customers' },
  { to: '/admin/transactions', label: 'Transactions' },
  { to: '/admin/transfer', label: 'Transfer' },
]

function useHealth() {
  const [ok, setOk] = useState(null)
  useEffect(() => {
    let alive = true
    const check = () =>
      fetch(`${API_ORIGIN}/health`)
        .then((r) => r.ok)
        .catch(() => false)
        .then((up) => { if (alive) setOk(up) })
    check()
    const timer = setInterval(check, 15000)
    return () => { alive = false; clearInterval(timer) }
  }, [])
  return ok
}

export default function AdminLayout() {
  const { logout } = useAuth()
  const health = useHealth()

  return (
    <div className="home-page">
      <header className="topbar">
        <span className="brand-small admin-brand">
          <span className="brand-chip" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"
                 strokeLinecap="round" strokeLinejoin="round">
              <path d="M4.5 19.5 17 7" /><path d="M19.5 19.5 7 7" />
              <path d="M15.2 5.6 18.4 8.8" /><path d="M5.6 8.8 8.8 5.6" />
            </svg>
          </span>
          Three Musketeers United · Admin
        </span>
        <div className="topbar-actions">
          <span className="health" title="API status">
            <span className={`health-dot ${health === null ? '' : health ? 'ok' : 'bad'}`} />
            {health === null ? 'checking…' : health ? 'API online' : 'API offline'}
          </span>
          <ThemeToggle />
          <button type="button" className="secondary" onClick={logout}>Sign out</button>
        </div>
      </header>

      <nav className="admin-nav" aria-label="Admin sections">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            className={({ isActive }) => (isActive ? 'admin-tab active' : 'admin-tab')}
          >
            {n.label}
          </NavLink>
        ))}
      </nav>

      <main className="home-card admin-main">
        <Outlet />
      </main>
    </div>
  )
}
