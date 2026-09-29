import { useEffect, useState } from 'react'
import { getCurrentUser, logout } from './api/authService.js'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'

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
      setUser(u)
      setChecking(false)
    })
  }, [])

  async function handleLogout() {
    await logout()
    setUser(null)
  }

  if (checking) return <div className="loading">Loading…</div>
  return user ? <Home user={user} onLogout={handleLogout} /> : <Login onLogin={setUser} />
}