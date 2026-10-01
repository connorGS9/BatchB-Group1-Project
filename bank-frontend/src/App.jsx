import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth.jsx'
import AdminApplications from './pages/AdminApplications.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import OpenAccount from './pages/OpenAccount.jsx'

function Loading() {
  return <div className="loading">Loading…</div>
}

// Gate for admin-only areas.
function RequireAdmin({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Loading />
  if (user?.role !== 'ADMIN') return <Navigate to="/adminlogin" replace />
  return children
}

// "/" — customers land here. Admins are sent to their area; anyone else sees the
// customer sign-in.
function RootRoute() {
  const { user, loading } = useAuth()
  if (loading) return <Loading />
  if (user?.role === 'ADMIN') return <Navigate to="/admin" replace />
  if (user) return <Home />
  return <Login admin={false} />
}

// "/adminlogin" — the admin door. Already-signed-in admins skip straight in.
function AdminLoginRoute() {
  const { user, loading } = useAuth()
  if (loading) return <Loading />
  if (user?.role === 'ADMIN') return <Navigate to="/admin" replace />
  return <Login admin />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RootRoute />} />
          <Route path="/adminlogin" element={<AdminLoginRoute />} />
          <Route path="/apply" element={<OpenAccount />} />
          {/* Admin area — expands into /admin/* in the next step. */}
          <Route path="/admin" element={<RequireAdmin><AdminApplications /></RequireAdmin>} />
          <Route path="/applications" element={<Navigate to="/admin" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
