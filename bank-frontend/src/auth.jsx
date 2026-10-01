import { createContext, useContext, useEffect, useState } from 'react'
import { getCurrentUser, logout as apiLogout } from './api/authService.js'

// One place that knows who's signed in. Loads the session once on mount and
// shares { user, loading, setUser, logout } with the whole app.
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // The legacy :8000 dashboard signs out via …/adminlogin?logout=1. Honor it
    // while that page still exists, then strip the flag from the URL.
    const params = new URLSearchParams(window.location.search)
    if (params.has('logout')) {
      apiLogout().finally(() => {
        window.history.replaceState({}, '', window.location.pathname)
        setUser(null)
        setLoading(false)
      })
      return
    }
    getCurrentUser().then((u) => {
      setUser(u)
      setLoading(false)
    })
  }, [])

  async function logout() {
    await apiLogout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
