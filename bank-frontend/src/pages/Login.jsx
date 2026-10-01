import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login, logout } from '../api/authService.js'
import { useAuth } from '../auth.jsx'
import BrandSlideshow from '../components/BrandSlideshow.jsx'

// One sign-in form, two doors:
//   /            -> customers only
//   /adminlogin  -> bank admins only  (admin = true)
// The role comes from the server (inside the JWT), so the check below is just to
// send people to the right page. The API itself still blocks customers from admin
// routes with 403, whatever page they used.
export default function Login({ admin = false }) {
  const { setUser } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!username.trim() || !password) {
      setError('Enter your username and password.')
      return
    }
    setLoading(true)
    try {
      const user = await login(username.trim(), password)
      const isAdmin = user.role === 'ADMIN'
      if (admin && !isAdmin) {
        await logout()
        setError('This sign-in is for bank administrators only. Customers sign in on the main page.')
        return
      }
      if (!admin && isAdmin) {
        await logout()
        setError('Administrators sign in at /adminlogin.')
        return
      }
      setUser(user)
      navigate(isAdmin ? '/admin' : '/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <section className="brand-panel" aria-hidden="true">
        <BrandSlideshow />
        <div className="brand-content">
          <div className="brand-mark">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"
                 strokeLinecap="round" strokeLinejoin="round">
              {/* Crossed rapiers — "all for one" */}
              <path d="M4.5 19.5 17 7" />
              <path d="M19.5 19.5 7 7" />
              <path d="M15.2 5.6 18.4 8.8" />
              <path d="M5.6 8.8 8.8 5.6" />
              <path d="M4.5 19.5 6.6 17.4" />
              <path d="M19.5 19.5 17.4 17.4" />
            </svg>
          </div>
          <div className="brand-words">
            <p className="brand-eyebrow">Est. for everyone</p>
            <h2>Three Musketeers United</h2>
            <p className="brand-motto">All for one.</p>
          </div>
        </div>
      </section>

      <main className="login-panel">
        <div className="login-stack">
        <form className="login-form" onSubmit={handleSubmit} noValidate>
          {admin && <p className="eyebrow">Administrator</p>}
          <h1>{admin ? 'Admin sign in' : 'Sign in'}</h1>
          <p className="subtitle">{admin ? 'Bank staff only.' : 'Welcome back.'}</p>

          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
            autoFocus
          />

          <label htmlFor="password">Password</label>
          <div className="password-row">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            <button
              type="button"
              className="show-toggle"
              onClick={() => setShowPassword((s) => !s)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? 'Hide' : 'Show'}
            </button>
          </div>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="primary" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="demo">
            {admin ? (
              <>Demo login: <code>admin</code> / <code>admin123</code></>
            ) : (
              <>Demo login: <code>john</code> / <code>password123</code></>
            )}
          </p>
          {!admin && (
            <p className="demo switch-door">
              New here? <Link to="/apply">Request to open an account</Link>
            </p>
          )}
          <p className="demo switch-door">
            {admin ? <Link to="/">Customer sign in</Link> : <Link to="/adminlogin">Bank staff? Admin sign in</Link>}
          </p>
        </form>

        {!admin && (
        <div className="login-features">
          <ul className="feature-list">
            <li className="feature">
              <span className="feature-ico" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
                     strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 2 11 13" />
                  <path d="M22 2 15 22 11 13 2 9 22 2Z" />
                </svg>
              </span>
              <div>
                <p className="feature-t">Send to friends</p>
                <p className="feature-s">Pay another account holder in a couple of taps.</p>
              </div>
            </li>
            <li className="feature">
              <span className="feature-ico" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
                     strokeLinecap="round" strokeLinejoin="round">
                  <path d="M7 7v10" />
                  <path d="M4 14l3 3 3-3" />
                  <path d="M17 17V7" />
                  <path d="M14 10l3-3 3 3" />
                </svg>
              </span>
              <div>
                <p className="feature-t">Money in &amp; out</p>
                <p className="feature-s">See your last 30 days at a glance.</p>
              </div>
            </li>
            <li className="feature">
              <span className="feature-ico" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
                     strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3 3 8l9 5 9-5-9-5Z" />
                  <path d="M3 13l9 5 9-5" />
                </svg>
              </span>
              <div>
                <p className="feature-t">All your accounts</p>
                <p className="feature-s">Balances and activity in one place.</p>
              </div>
            </li>
          </ul>
        </div>
        )}
        </div>
      </main>
    </div>
  )
}