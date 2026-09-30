import { useCallback, useEffect, useState } from 'react'
import { getAllAccounts, getCustomer, getMyAccounts, getMyTransactions, getToken } from '../api/authService.js'
import Accounts from '../components/Accounts.jsx'
import SendMoney from '../components/SendMoney.jsx'
import Settings from '../components/Settings.jsx'

const DASHBOARD_URL = 'http://localhost:8000/'
const TABS = [
  { id: 'accounts', label: 'Accounts' },
  { id: 'send', label: 'Send money' },
  { id: 'settings', label: 'Settings' },
]

export default function Home({ user, onLogout }) {
  const isAdmin = user.role === 'ADMIN'
  const [tab, setTab] = useState('accounts')
  const [customer, setCustomer] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [transactions, setTransactions] = useState([])
  const [allAccounts, setAllAccounts] = useState([])
  const [error, setError] = useState('')

  // Load profile, accounts and activity from the API
  const load = useCallback(async () => {
    if (!user.customer_id) return
    try {
      const [c, accts, everyone] = await Promise.all([
        getCustomer(user.customer_id),
        getMyAccounts(user.customer_id),
        getAllAccounts(),
      ])
      setCustomer(c)
      setAccounts(accts)
      setAllAccounts(everyone)
      setTransactions(await getMyTransactions(accts.map((a) => a.id)))
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }, [user.customer_id])

  useEffect(() => {
    load()
  }, [load])

  const firstName = customer?.first_name || user.full_name.split(' ')[0]

  return (
    <div className="home-page">
      <header className="topbar">
        <span className="brand-small">Group 1 Bank</span>
        <button type="button" className="secondary" onClick={onLogout}>
          Sign out
        </button>
      </header>

      <main className="home-card">
        <p className="eyebrow">{isAdmin ? 'Administrator' : 'Customer'}</p>
        <h1>Hi, {isAdmin ? 'Admin' : firstName}</h1>

        {isAdmin && (
          <>
            <p>You're signed in as <strong>{user.username}</strong>.</p>
            {/* The dashboard is on another port, so hand it the login token after the "#"
                (the part after # is never sent to any server). */}
            <a className="primary-link" href={`${DASHBOARD_URL}#token=${encodeURIComponent(getToken() || '')}`}>
              Open the admin dashboard
            </a>
          </>
        )}

        {error && <p className="error" role="alert">{error}</p>}

        {!isAdmin && customer && (
          <>
            <nav className="tabs" aria-label="Sections">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className={tab === t.id ? 'tab active' : 'tab'}
                  aria-current={tab === t.id ? 'page' : undefined}
                  onClick={() => setTab(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </nav>

            {tab === 'accounts' && <Accounts accounts={accounts} allAccounts={allAccounts} transactions={transactions} />}
            {tab === 'send' && <SendMoney accounts={accounts} onSent={load} />}
            {tab === 'settings' && <Settings customer={customer} onSaved={setCustomer} />}
          </>
        )}
      </main>
    </div>
  )
}