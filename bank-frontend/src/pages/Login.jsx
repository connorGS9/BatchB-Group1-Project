import { useState } from 'react'
import { login } from '../api/authService.js'

export default function Login({ onLogin }) {
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
      onLogin(user)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <section className="brand-panel" aria-hidden="true">
        <div className="brand-mark">G1</div>
        <h2>Group 1 Bank</h2>
        <p>Accounts, transfers and branch banking in one place.</p>
      </section>

      <main className="login-panel">
        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <h1>Sign in</h1>
          <p className="subtitle">Welcome back. Enter your details to continue.</p>

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
            Demo logins: <code>john</code> / <code>password123</code> · <code>admin</code> /{' '}
            <code>admin123</code>
          </p>
        </form>
      </main>
    </div>
  )
}