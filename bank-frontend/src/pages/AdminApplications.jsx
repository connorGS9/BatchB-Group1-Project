import { useCallback, useEffect, useState } from 'react'
import {
  approveApplication, declineApplication, getApplications, getToken,
} from '../api/authService.js'
import { useAuth } from '../auth.jsx'
import { money } from '../components/format.js'

// The admin dashboard (accounts/customers/transactions) still lives on the API
// origin; this page links to it and hands over the login token after the "#".
const DASHBOARD_URL = 'http://localhost:8000/'

function fmtDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit',
  })
}

export default function AdminApplications() {
  const { logout } = useAuth()
  const [apps, setApps] = useState([])
  const [tab, setTab] = useState('review')
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState(null)
  const [decliningId, setDecliningId] = useState(null)
  const [balances, setBalances] = useState({}) // id -> opening balance (string)
  const [notes, setNotes] = useState({})       // id -> decline reason (string)

  const load = useCallback(async () => {
    try {
      setApps(await getApplications())
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const pending = apps.filter((a) => a.status === 'PENDING')
  const decided = apps
    .filter((a) => a.status !== 'PENDING')
    .sort((a, b) => new Date(b.decided_at) - new Date(a.decided_at))

  async function approve(a) {
    setBusyId(a.id)
    setError('')
    try {
      const amount = Math.max(0, Number(balances[a.id]) || 0)
      await approveApplication(a.id, amount)
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusyId(null)
    }
  }

  async function decline(a) {
    setBusyId(a.id)
    setError('')
    try {
      await declineApplication(a.id, (notes[a.id] || '').trim() || null)
      setDecliningId(null)
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusyId(null)
    }
  }

  function openDashboard() {
    window.location.href = `${DASHBOARD_URL}#token=${encodeURIComponent(getToken() || '')}`
  }

  return (
    <div className="home-page">
      <header className="topbar">
        <span className="brand-small">Three Musketeers United · Admin</span>
        <div className="topbar-actions">
          <button type="button" className="secondary" onClick={openDashboard}>Open full dashboard</button>
          <button type="button" className="secondary" onClick={logout}>Sign out</button>
        </div>
      </header>

      <main className="home-card">
        <p className="eyebrow">Administrator</p>
        <h1>Account applications</h1>

        <nav className="tabs" aria-label="Applications views">
          <button type="button" className={tab === 'review' ? 'tab active' : 'tab'} onClick={() => setTab('review')}>
            To review ({pending.length})
          </button>
          <button type="button" className={tab === 'log' ? 'tab active' : 'tab'} onClick={() => setTab('log')}>
            Decision log ({decided.length})
          </button>
        </nav>

        {error && <p className="error" role="alert">{error}</p>}

        {tab === 'review' ? (
          pending.length === 0 ? (
            <p className="muted">No applications waiting for review.</p>
          ) : (
            pending.map((a) => (
              <section className="panel" key={a.id}>
                <div className="app-head">
                  <h2>{a.first_name} {a.last_name}</h2>
                  <span className="muted">#{a.id} · {fmtDate(a.created_at)}</span>
                </div>
                <dl className="details">
                  <dt>Email</dt><dd>{a.email}</dd>
                  <dt>Phone</dt><dd>{a.phone}</dd>
                  <dt>Address</dt><dd>{a.address}</dd>
                  <dt>Base salary</dt><dd>{money(a.base_salary)}</dd>
                  <dt>Branch</dt><dd>#{a.branch_id}</dd>
                  <dt>Username</dt><dd>{a.username}</dd>
                </dl>

                {decliningId === a.id ? (
                  <div className="decline-box">
                    <label htmlFor={`note-${a.id}`}>Reason for declining (optional)</label>
                    <textarea
                      id={`note-${a.id}`}
                      rows={2}
                      value={notes[a.id] || ''}
                      onChange={(e) => setNotes((n) => ({ ...n, [a.id]: e.target.value }))}
                      placeholder="e.g. Could not verify the address."
                    />
                    <div className="button-row">
                      <button type="button" className="danger-btn" disabled={busyId === a.id} onClick={() => decline(a)}>
                        {busyId === a.id ? 'Declining…' : 'Confirm decline'}
                      </button>
                      <button type="button" className="secondary" disabled={busyId === a.id} onClick={() => setDecliningId(null)}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="approve-row">
                    <label htmlFor={`bal-${a.id}`}>Opening balance</label>
                    <input
                      id={`bal-${a.id}`}
                      type="number" min="0" step="0.01" placeholder="0.00"
                      value={balances[a.id] ?? ''}
                      onChange={(e) => setBalances((b) => ({ ...b, [a.id]: e.target.value }))}
                    />
                    <div className="button-row">
                      <button type="button" className="primary" disabled={busyId === a.id} onClick={() => approve(a)}>
                        {busyId === a.id ? 'Approving…' : 'Approve'}
                      </button>
                      <button type="button" className="secondary" onClick={() => setDecliningId(a.id)}>
                        Decline
                      </button>
                    </div>
                  </div>
                )}
              </section>
            ))
          )
        ) : decided.length === 0 ? (
          <p className="muted">No decisions yet.</p>
        ) : (
          <ul className="log-list">
            {decided.map((a) => {
              const approved = a.status === 'APPROVED'
              return (
                <li className="log-item" key={a.id}>
                  <div>
                    <p className="log-who">
                      <span className={approved ? 'tag tag-ok' : 'tag tag-no'}>
                        {approved ? 'Allowed' : 'Disallowed'}
                      </span>
                      {a.first_name} {a.last_name} <span className="muted">(@{a.username})</span>
                    </p>
                    <p className="log-meta">
                      {approved
                        ? `Approved → customer #${a.customer_id}, account #${a.account_id}`
                        : `Declined${a.decision_note ? ` — “${a.decision_note}”` : ' — no reason given'}`}
                    </p>
                  </div>
                  <div className="log-side">
                    <span className="muted">by {a.decided_by || '—'}</span>
                    <span className="muted">{fmtDate(a.decided_at)}</span>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </main>
    </div>
  )
}
