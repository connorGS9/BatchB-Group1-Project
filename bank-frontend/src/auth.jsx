import { createContext, useContext, useEffect, useState } from 'react'
import { getCurrentUser, logout as apiLogout } from './api/authService.js'

// One place that knows who's signed in. Loads the session once on mount and
// shares { user, loading, setUser, logout } with the whole app.
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
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
