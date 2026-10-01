import { useCallback, useEffect, useState } from 'react'
import { getAllAccounts, getCustomer, getMyAccounts, getMyTransactions } from '../api/authService.js'
import { useAuth } from '../auth.jsx'
import Accounts from '../components/Accounts.jsx'
import Dashboard from '../components/Dashboard.jsx'
import SendMoney from '../components/SendMoney.jsx'
import Settings from '../components/Settings.jsx'
import ThemeToggle from '../components/ThemeToggle.jsx'

const TABS = [
  { id: 'accounts', label: 'Accounts' },
  { id: 'send', label: 'Send money' },
  { id: 'settings', label: 'Settings' },
]

export default function Home() {
  const { user, logout } = useAuth()
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
        <span className="brand-small">Three Musketeers United</span>
        <div className="topbar-actions">
          <ThemeToggle />
          <button type="button" className="secondary" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="home-card">
        <p className="eyebrow">Customer</p>
        <h1>Hi, {firstName}</h1>

        {error && <p className="error" role="alert">{error}</p>}

        {customer && (
          <>
            <Dashboard
              accounts={accounts}
              directory={allAccounts}
              transactions={transactions}
              onDone={load}
            />

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