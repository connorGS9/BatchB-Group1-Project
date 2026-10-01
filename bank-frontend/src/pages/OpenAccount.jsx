import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPublicBranches, submitApplication } from '../api/authService.js'
import BrandSlideshow from '../components/BrandSlideshow.jsx'

const EMPTY = {
  first_name: '', last_name: '', email: '', phone: '', address: '',
  base_salary: '', branch_id: '', username: '', password: '',
}

// Public "request to open an account" page. Submitting creates a PENDING
// application an admin reviews — no login is created until they approve it.
export default function OpenAccount() {
  const [form, setForm] = useState(EMPTY)
  const [branches, setBranches] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('') // calm info (e.g. already in review)
  const [done, setDone] = useState(false)

  useEffect(() => {
    getPublicBranches()
      .then((bs) => {
        setBranches(bs)
        setForm((f) => ({ ...f, branch_id: bs[0]?.id ?? '' }))
      })
      .catch((err) => setError(err.message))
  }, [])

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setNotice('')
    setLoading(true)
    try {
      await submitApplication({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        address: form.address.trim(),
        base_salary: Number(form.base_salary),
        branch_id: Number(form.branch_id),
        username: form.username.trim(),
        password: form.password,
      })
      setDone(true)
    } catch (err) {
      // 409 = you already have one in review. That's not a failure — show it calmly.
      if (err.status === 409) setNotice(err.message)
      else setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <section className="brand-panel" aria-hidden="true">
        <BrandSlideshow />
        <div className="brand-content">
          <div className="brand-words">
            <p className="brand-eyebrow">Est. for everyone</p>
            <h2>Three Musketeers United</h2>
            <p className="brand-motto">All for one.</p>
          </div>
        </div>
      </section>

      <main className="login-panel">
        <div className="login-stack">
          {done ? (
            <div className="apply-done">
              <h1>Application received</h1>
              <p className="subtitle">
                Thanks, {form.first_name || 'there'}. A banker will review your request and set up
                your login. You'll be able to sign in with the username you chose once it's approved.
              </p>
              <p className="demo"><Link to="/">Back to sign in</Link></p>
            </div>
          ) : (
            <form className="login-form" onSubmit={handleSubmit} noValidate>
              <h1>Open an account</h1>
              <p className="subtitle">Tell us about you and pick a branch. No deposit needed yet.</p>

              <div className="apply-grid">
                <div className="apply-field">
                  <label htmlFor="first_name">First name</label>
                  <input id="first_name" value={form.first_name} onChange={set('first_name')} disabled={loading} autoFocus />
                </div>
                <div className="apply-field">
                  <label htmlFor="last_name">Last name</label>
                  <input id="last_name" value={form.last_name} onChange={set('last_name')} disabled={loading} />
                </div>
              </div>

              <label htmlFor="email">Email</label>
              <input id="email" type="email" autoComplete="email" value={form.email} onChange={set('email')} disabled={loading} />

              <label htmlFor="phone">Phone</label>
              <input id="phone" value={form.phone} onChange={set('phone')} placeholder="555-0100" disabled={loading} />

              <label htmlFor="address">Address</label>
              <input id="address" value={form.address} onChange={set('address')} disabled={loading} />

              <div className="apply-grid">
                <div className="apply-field">
                  <label htmlFor="base_salary">Base salary (USD)</label>
                  <input id="base_salary" type="number" min="0" step="1" value={form.base_salary} onChange={set('base_salary')} placeholder="0" disabled={loading} />
                </div>
                <div className="apply-field">
                  <label htmlFor="branch_id">Branch</label>
                  <select id="branch_id" value={form.branch_id} onChange={set('branch_id')} disabled={loading || branches.length === 0}>
                    {branches.length === 0 && <option value="">Loading…</option>}
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name} · {b.city}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="apply-grid">
                <div className="apply-field">
                  <label htmlFor="username">Choose a username</label>
                  <input id="username" autoComplete="username" value={form.username} onChange={set('username')} disabled={loading} />
                </div>
                <div className="apply-field">
                  <label htmlFor="password">Choose a password</label>
                  <input id="password" type="password" autoComplete="new-password" value={form.password} onChange={set('password')} disabled={loading} />
                </div>
              </div>

              {notice && <p className="notice" role="status">{notice}</p>}
              {error && <p className="error" role="alert">{error}</p>}

              <button type="submit" className="primary" disabled={loading}>
                {loading ? 'Submitting…' : 'Submit application'}
              </button>

              <p className="demo"><Link to="/">Already bank with us? Sign in</Link></p>
            </form>
          )}
        </div>
      </main>
    </div>
  )
}
