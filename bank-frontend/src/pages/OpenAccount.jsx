import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPublicBranches, submitApplication } from '../api/authService.js'
import BrandSlideshow from '../components/BrandSlideshow.jsx'

const EMPTY = {
  first_name: '', last_name: '', email: '', phone: '', address: '',
  base_salary: '', branch_id: '', username: '', password: '',
}

// Rules mirror the backend (models/application.py) so the form catches problems
// before submitting and explains each one in plain language.
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const PHONE_RE = /^[0-9+()\-.\s]{7,20}$/
const USERNAME_RE = /^[A-Za-z0-9_]+$/
const FIELD_ORDER = ['first_name', 'last_name', 'email', 'phone', 'address', 'base_salary', 'branch_id', 'username', 'password']

function validate(form) {
  const e = {}
  if (!form.first_name.trim()) e.first_name = 'Enter your first name.'
  else if (form.first_name.trim().length > 50) e.first_name = 'Keep this under 50 characters.'
  if (!form.last_name.trim()) e.last_name = 'Enter your last name.'
  else if (form.last_name.trim().length > 50) e.last_name = 'Keep this under 50 characters.'
  if (!EMAIL_RE.test(form.email.trim())) e.email = 'Enter a valid email, like you@example.com.'
  if (!PHONE_RE.test(form.phone.trim())) e.phone = 'Enter a 7–20 digit phone number (spaces, + ( ) - . are fine).'
  if (!form.address.trim()) e.address = 'Enter your address.'
  else if (form.address.trim().length > 200) e.address = 'Keep this under 200 characters.'
  const salary = Number(form.base_salary)
  if (form.base_salary === '' || Number.isNaN(salary) || salary < 0) e.base_salary = 'Enter an amount of 0 or more.'
  if (!form.branch_id) e.branch_id = 'Choose a branch.'
  const u = form.username.trim()
  if (u.length < 3 || u.length > 30 || !USERNAME_RE.test(u)) {
    e.username = 'Use 3–30 letters, numbers or underscores.'
  }
  if (form.password.length < 8) e.password = 'Use at least 8 characters.'
  else if (form.password.length > 128) e.password = 'Keep this under 128 characters.'
  return e
}

// Public "request to open an account" page. Submitting creates a PENDING
// application an admin reviews — no login is created until they approve it.
export default function OpenAccount() {
  const [form, setForm] = useState(EMPTY)
  const [fieldErrors, setFieldErrors] = useState({})
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

  // Update a field and clear its error as the person fixes it.
  function set(field) {
    return (e) => {
      const { value } = e.target
      setForm((f) => ({ ...f, [field]: value }))
      setFieldErrors((fe) => (fe[field] ? { ...fe, [field]: undefined } : fe))
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setNotice('')

    const errs = validate(form)
    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs)
      const first = FIELD_ORDER.find((f) => errs[f])
      if (first) document.getElementById(first)?.focus()
      return
    }
    setFieldErrors({})

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

  // Small helper to render a field's inline error.
  const errOf = (field) =>
    fieldErrors[field] ? <p className="field-error" role="alert">{fieldErrors[field]}</p> : null
  const cls = (field) => (fieldErrors[field] ? 'input-error' : undefined)

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
                  <input id="first_name" className={cls('first_name')} aria-invalid={!!fieldErrors.first_name} value={form.first_name} onChange={set('first_name')} disabled={loading} autoFocus />
                  {errOf('first_name')}
                </div>
                <div className="apply-field">
                  <label htmlFor="last_name">Last name</label>
                  <input id="last_name" className={cls('last_name')} aria-invalid={!!fieldErrors.last_name} value={form.last_name} onChange={set('last_name')} disabled={loading} />
                  {errOf('last_name')}
                </div>
              </div>

              <label htmlFor="email">Email</label>
              <input id="email" type="email" autoComplete="email" className={cls('email')} aria-invalid={!!fieldErrors.email} value={form.email} onChange={set('email')} disabled={loading} />
              {errOf('email')}

              <label htmlFor="phone">Phone</label>
              <input id="phone" className={cls('phone')} aria-invalid={!!fieldErrors.phone} value={form.phone} onChange={set('phone')} placeholder="555-0100" disabled={loading} />
              {errOf('phone')}

              <label htmlFor="address">Address</label>
              <input id="address" className={cls('address')} aria-invalid={!!fieldErrors.address} value={form.address} onChange={set('address')} disabled={loading} />
              {errOf('address')}

              <div className="apply-grid">
                <div className="apply-field">
                  <label htmlFor="base_salary">Base salary (USD)</label>
                  <input id="base_salary" type="number" min="0" step="1" className={cls('base_salary')} aria-invalid={!!fieldErrors.base_salary} value={form.base_salary} onChange={set('base_salary')} placeholder="0" disabled={loading} />
                  {errOf('base_salary')}
                </div>
                <div className="apply-field">
                  <label htmlFor="branch_id">Branch</label>
                  <select id="branch_id" className={cls('branch_id')} aria-invalid={!!fieldErrors.branch_id} value={form.branch_id} onChange={set('branch_id')} disabled={loading || branches.length === 0}>
                    {branches.length === 0 && <option value="">Loading…</option>}
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name} · {b.city}</option>
                    ))}
                  </select>
                  {errOf('branch_id')}
                </div>
              </div>

              <div className="apply-grid">
                <div className="apply-field">
                  <label htmlFor="username">Choose a username</label>
                  <input id="username" autoComplete="username" className={cls('username')} aria-invalid={!!fieldErrors.username} value={form.username} onChange={set('username')} disabled={loading} />
                  {errOf('username')}
                </div>
                <div className="apply-field">
                  <label htmlFor="password">Choose a password</label>
                  <input id="password" type="password" autoComplete="new-password" className={cls('password')} aria-invalid={!!fieldErrors.password} value={form.password} onChange={set('password')} disabled={loading} />
                  {errOf('password')}
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
