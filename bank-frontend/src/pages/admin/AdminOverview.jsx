import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAccounts, getApplications, getCustomers, getTransactions } from '../../api/authService.js'
import { money } from '../../components/format.js'

// At-a-glance totals for the admin, built from the existing list endpoints.
export default function AdminOverview() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getAccounts(), getCustomers(), getTransactions(), getApplications('PENDING')])
      .then(([accounts, customers, transactions, pending]) => {
        setStats({
          accounts: accounts.length,
          // Headline funds = live money, so exclude deactivated accounts.
          balance: accounts.filter((a) => a.is_active).reduce((sum, a) => sum + a.balance, 0),
          customers: customers.length,
          transactions: transactions.length,
          pending: pending.length,
        })
      })
      .catch((e) => setError(e.message))
  }, [])

  return (
    <>
      <h1>Overview</h1>
      <p className="muted">Everything across the bank, at a glance.</p>

      {error && <p className="error" role="alert">{error}</p>}

      <ul className="stat-tiles admin-tiles">
        <li className="stat">
          <span className="stat-label">Pending applications</span>
          <span className={`stat-value ${stats?.pending ? 'alert' : ''}`}>{stats ? stats.pending : '–'}</span>
        </li>
        <li className="stat">
          <span className="stat-label">Accounts</span>
          <span className="stat-value">{stats ? stats.accounts : '–'}</span>
        </li>
        <li className="stat">
          <span className="stat-label">Total balance</span>
          <span className="stat-value">{stats ? money(stats.balance) : '–'}</span>
        </li>
        <li className="stat">
          <span className="stat-label">Customers</span>
          <span className="stat-value">{stats ? stats.customers : '–'}</span>
        </li>
        <li className="stat">
          <span className="stat-label">Transactions</span>
          <span className="stat-value">{stats ? stats.transactions : '–'}</span>
        </li>
      </ul>

      {stats?.pending > 0 && (
        <p className="overview-cta">
          <Link to="/admin/applications">Review {stats.pending} pending application{stats.pending === 1 ? '' : 's'} →</Link>
        </p>
      )}
    </>
  )
}
