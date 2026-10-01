import { useEffect, useState } from 'react'
import { getCurrentUser, getToken, logout } from './api/authService.js'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'

// Two sign-in pages without a router library: we just look at the URL path.
const ADMIN_PATH = '/adminlogin'
const onAdminPage = window.location.pathname.replace(/\/+$/, '') === ADMIN_PATH

// Admins go straight to the admin dashboard (served by the API on port 8000).
// The login token rides after the "#", which is never sent to any server.
const DASHBOARD_URL = 'http://localhost:8000/'
function openAdminDashboard() {
  window.location.replace(`${DASHBOARD_URL}#token=${encodeURIComponent(getToken() || '')}`)
}

export default function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(true)

  // On page load, see if we're still logged in from before
  useEffect(() => {
    // Coming back from the admin dashboard's "Sign out" (…/?logout=1):
    // clear the session, strip the flag from the URL, and show the login screen.
    const params = new URLSearchParams(window.location.search)
    if (params.has('logout')) {
      logout().finally(() => {
        window.history.replaceState({}, '', window.location.pathname)
        setUser(null)
        setChecking(false)
      })
      return
    }
    getCurrentUser().then((u) => {
      // Already signed in as admin: /adminlogin -> dashboard, customer page -> /adminlogin.
      if (u?.role === 'ADMIN') {
        if (onAdminPage) openAdminDashboard()
        else window.location.replace(ADMIN_PATH)
        return
      }
      // Signed in as a customer but opened /adminlogin -> show the admin sign-in form.
      setUser(onAdminPage && u?.role !== 'ADMIN' ? null : u)
      setChecking(false)
    })
  }, [])

  // After signing in: admins open the dashboard, customers see their home page.
  function handleLogin(u) {
    if (u.role === 'ADMIN') openAdminDashboard()
    else setUser(u)
  }

  async function handleLogout() {
    await logout()
    setUser(null)
  }

  if (checking) return <div className="loading">Loading…</div>
  return user ? <Home user={user} onLogout={handleLogout} /> : <Login admin={onAdminPage} onLogin={handleLogin} />
}